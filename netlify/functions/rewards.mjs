// Admin API for reward pictures. Checks ADMIN_PASSWORD, then edits the GitHub repo with GITHUB_TOKEN.
// Both are Netlify environment variables, so neither ever reaches the browser or the public repo.
import { createHash, timingSafeEqual } from "node:crypto";

const OWNER = "brouiht-ui", REPO = "logic-flashcards", BRANCH = "main", MANIFEST = "rewards.json", DIR = "rewards";
const API = `https://api.github.com/repos/${OWNER}/${REPO}/contents/`;

const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", "cache-control": "no-store" } });
const sha256 = s => createHash("sha256").update(String(s)).digest();
const encPath = p => p.split("/").map(encodeURIComponent).join("/");

function passwordOk(given) {
  const real = process.env.ADMIN_PASSWORD;
  if (!real || typeof given !== "string") return false;
  return timingSafeEqual(sha256(given), sha256(real));
}

async function gh(path, opts = {}) {
  const res = await fetch(API + encPath(path) + (opts.method ? "" : `?ref=${BRANCH}`), {
    ...opts,
    headers: { Authorization: `Bearer ${process.env.GITHUB_TOKEN}`, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "logic-flashcards-admin" },
  });
  if (res.status === 404 && !opts.method) return null;
  if (!res.ok) {
    const hint = res.status === 401 ? " (GITHUB_TOKEN is wrong or expired)" : res.status === 403 ? " (GITHUB_TOKEN needs Contents: Read and write on logic-flashcards)" : "";
    throw new Error(`GitHub error ${res.status}${hint}`);
  }
  return res.status === 204 ? {} : res.json();
}

async function readManifest() {
  const f = await gh(MANIFEST);
  if (!f) return { data: { images: [] }, sha: null };
  const data = JSON.parse(Buffer.from(f.content, "base64").toString("utf8"));
  if (!Array.isArray(data.images)) data.images = [];
  return { data, sha: f.sha };
}

async function writeManifest(data, sha, message) {
  const body = { message, branch: BRANCH, content: Buffer.from(JSON.stringify(data, null, 2) + "\n").toString("base64") };
  if (sha) body.sha = sha;
  await gh(MANIFEST, { method: "PUT", body: JSON.stringify(body) });
}

const rawUrl = p => `https://raw.githubusercontent.com/${OWNER}/${REPO}/${BRANCH}/${encPath(p)}`;

export default async req => {
  if (req.method !== "POST") return json({ error: "Use POST" }, 405);
  let body;
  try { body = await req.json(); } catch { return json({ error: "Bad request" }, 400); }

  if (!passwordOk(body.password)) {
    await new Promise(r => setTimeout(r, 1000)); // slow down guessing
    return json({ error: process.env.ADMIN_PASSWORD ? "Wrong password" : "ADMIN_PASSWORD is not set in Netlify" }, 401);
  }
  if (!process.env.GITHUB_TOKEN) return json({ error: "GITHUB_TOKEN is not set in Netlify" }, 500);

  try {
    if (body.action === "list") {
      const { data } = await readManifest();
      return json({ images: data.images.map(p => ({ path: p, url: rawUrl(p) })) });
    }

    if (body.action === "add") {
      const ext = (String(body.name || "").match(/\.(png|jpe?g|gif|webp)$/i) || [".jpg"])[0].toLowerCase();
      const base = String(body.name || "reward").replace(/\.[^.]+$/, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 40) || "reward";
      if (typeof body.data !== "string" || !body.data) return json({ error: "No picture data" }, 400);
      const path = `${DIR}/${Date.now()}-${base}${ext}`;
      await gh(path, { method: "PUT", body: JSON.stringify({ message: `Add reward ${path}`, branch: BRANCH, content: body.data }) });
      const { data, sha } = await readManifest();
      data.images.push(path);
      await writeManifest(data, sha, `Add reward ${path} to list`);
      return json({ ok: true, path });
    }

    if (body.action === "remove") {
      const { data, sha } = await readManifest();
      const path = String(body.path || "");
      if (!data.images.includes(path)) return json({ error: "Not in the rewards list" }, 404);
      data.images = data.images.filter(p => p !== path);
      await writeManifest(data, sha, `Remove reward ${path} from list`);
      const f = await gh(path);
      if (f) await gh(path, { method: "DELETE", body: JSON.stringify({ message: `Delete reward ${path}`, branch: BRANCH, sha: f.sha }) });
      return json({ ok: true });
    }

    return json({ error: "Unknown action" }, 400);
  } catch (e) {
    return json({ error: e.message }, 502);
  }
};
