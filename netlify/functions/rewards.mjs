// Admin API for reward pictures and videos. Checks ADMIN_PASSWORD, then edits the GitHub repo with GITHUB_TOKEN.
// Both are Netlify environment variables, so neither ever reaches the browser or the public repo.
//
// Netlify caps a request at ~6 MB, so the admin page uploads files in pieces ("blob" calls, which create
// GitHub blobs without committing), then one "commit" call writes them all plus rewards.json in a single
// commit, so Netlify redeploys once per upload.
//
// rewards.json: { images: [...], punishments: [...] }, entries are "path.png" or { type: "video", id, mime, parts: [...] }.
// "images" are rewards for right answers, "punishments" show on wrong answers; requests pick one with bucket.
import { createHash, timingSafeEqual } from "node:crypto";

const OWNER = "brouiht-ui", REPO = "logic-flashcards", BRANCH = "main", MANIFEST = "rewards.json";
const BUCKETS = { rewards: { key: "images", dir: "rewards" }, punishments: { key: "punishments", dir: "punishments" } };
const BASE = `https://api.github.com/repos/${OWNER}/${REPO}`;

const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", "cache-control": "no-store" } });
const sha256 = s => createHash("sha256").update(String(s)).digest();
const encPath = p => p.split("/").map(encodeURIComponent).join("/");
const rawUrl = p => `https://raw.githubusercontent.com/${OWNER}/${REPO}/${BRANCH}/${encPath(p)}`;
const entryId = e => typeof e === "string" ? e : e.id;
const entryPaths = e => typeof e === "string" ? [e] : e.parts;

function passwordOk(given) {
  const real = process.env.ADMIN_PASSWORD;
  if (!real || typeof given !== "string") return false;
  return timingSafeEqual(sha256(given), sha256(real));
}

async function gh(path, opts = {}) {
  const res = await fetch(BASE + path, {
    ...opts,
    headers: { Authorization: `Bearer ${process.env.GITHUB_TOKEN}`, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "logic-flashcards-admin" },
  });
  if (res.status === 404 && opts.allow404) return null;
  if (!res.ok) {
    const hint = res.status === 401 ? " (GITHUB_TOKEN is wrong or expired)" : res.status === 403 ? " (GITHUB_TOKEN needs Contents: Read and write on logic-flashcards)" : "";
    const err = new Error(`GitHub error ${res.status}${hint}`);
    err.status = res.status;
    throw err;
  }
  return res.status === 204 ? {} : res.json();
}

async function readManifest(ref = BRANCH) {
  const f = await gh(`/contents/${MANIFEST}?ref=${ref}`, { allow404: true });
  const data = f ? JSON.parse(Buffer.from(f.content, "base64").toString("utf8")) : { images: [] };
  for (const b of Object.values(BUCKETS)) if (!Array.isArray(data[b.key])) data[b.key] = [];
  return data;
}

// One commit that applies tree changes and rewrites rewards.json via edit(manifest). Retries if main moved.
async function commit(message, changes, edit) {
  for (let attempt = 0; attempt < 3; attempt++) {
    const ref = await gh(`/git/ref/heads/${BRANCH}`);
    const head = await gh(`/git/commits/${ref.object.sha}`);
    const manifest = await readManifest(ref.object.sha);
    const result = edit(manifest);
    if (result === false) return false; // nothing to change
    const tree = await gh(`/git/trees`, {
      method: "POST",
      body: JSON.stringify({
        base_tree: head.tree.sha,
        tree: [
          ...changes(manifest),
          { path: MANIFEST, mode: "100644", type: "blob", content: JSON.stringify(manifest, null, 2) + "\n" },
        ],
      }),
    });
    const c = await gh(`/git/commits`, { method: "POST", body: JSON.stringify({ message, tree: tree.sha, parents: [ref.object.sha] }) });
    try {
      await gh(`/git/refs/heads/${BRANCH}`, { method: "PATCH", body: JSON.stringify({ sha: c.sha }) });
      return result;
    } catch (e) {
      if (e.status !== 422) throw e; // 422 = someone else committed first; rebuild on the new head
    }
  }
  throw new Error("The repo kept changing while saving. Try again.");
}

const clean = name => String(name || "reward").replace(/\.[^.]+$/, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40) || "reward";

export default async req => {
  if (req.method !== "POST") return json({ error: "Use POST" }, 405);
  let body;
  try { body = await req.json(); } catch { return json({ error: "Bad request (the piece may be too big)" }, 400); }

  if (!passwordOk(body.password)) {
    await new Promise(r => setTimeout(r, 1000)); // slow down guessing
    return json({ error: process.env.ADMIN_PASSWORD ? "Wrong password" : "ADMIN_PASSWORD is not set in Netlify" }, 401);
  }
  if (!process.env.GITHUB_TOKEN) return json({ error: "GITHUB_TOKEN is not set in Netlify" }, 500);

  const bucket = BUCKETS[body.bucket] || BUCKETS.rewards, KEY = bucket.key, DIR = bucket.dir;
  try {
    if (body.action === "list") {
      const data = await readManifest();
      return json({
        images: data[KEY].map(e => typeof e === "string"
          ? { type: "image", id: e, url: rawUrl(e) }
          : { type: "video", id: e.id, mime: e.mime, parts: e.parts.length, size: e.size || null }),
      });
    }

    // upload one piece; returns its blob sha (no commit yet)
    if (body.action === "blob") {
      if (typeof body.data !== "string" || !body.data) return json({ error: "No data" }, 400);
      const b = await gh(`/git/blobs`, { method: "POST", body: JSON.stringify({ content: body.data, encoding: "base64" }) });
      return json({ sha: b.sha });
    }

    // commit uploaded pieces as one reward
    if (body.action === "commit") {
      const shas = Array.isArray(body.shas) ? body.shas.filter(s => /^[0-9a-f]{40}$/.test(s)) : [];
      if (!shas.length || shas.length !== (body.shas || []).length) return json({ error: "Missing pieces" }, 400);
      const stamp = Date.now(), base = clean(body.name);
      let entry, files;
      if (body.kind === "video") {
        const mime = /^video\/[\w.+-]+$/.test(body.mime || "") ? body.mime : "video/mp4";
        const id = `${DIR}/${stamp}-${base}`;
        files = shas.map((sha, i) => ({ path: `${id}/part${String(i).padStart(3, "0")}.bin`, sha }));
        entry = { type: "video", id, mime, size: Number(body.size) || null, parts: files.map(f => f.path) };
      } else {
        if (shas.length !== 1) return json({ error: "Pictures upload as one piece" }, 400);
        const ext = (String(body.name || "").match(/\.(png|jpe?g|gif|webp)$/i) || [".jpg"])[0].toLowerCase();
        entry = `${DIR}/${stamp}-${base}${ext}`;
        files = [{ path: entry, sha: shas[0] }];
      }
      await commit(`Add reward ${entryId(entry)}`,
        () => files.map(f => ({ path: f.path, mode: "100644", type: "blob", sha: f.sha })),
        m => { m[KEY].push(entry); });
      return json({ ok: true, id: entryId(entry) });
    }

    if (body.action === "remove") {
      const id = String(body.id || "");
      let gone = null;
      await commit(`Remove reward ${id}`,
        m => gone ? entryPaths(gone).map(path => ({ path, mode: "100644", type: "blob", sha: null })) : [],
        m => {
          gone = m[KEY].find(e => entryId(e) === id) || null;
          if (!gone) return false;
          m[KEY] = m[KEY].filter(e => entryId(e) !== id);
        });
      return gone ? json({ ok: true }) : json({ error: "Not in this list" }, 404);
    }

    return json({ error: "Unknown action" }, 400);
  } catch (e) {
    return json({ error: e.message }, 502);
  }
};
