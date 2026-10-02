"""Builds logic-flashcards.pdf: schedule, 24 duplex flashcards, practice quiz + key."""
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Frame, KeepInFrame
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor, black, white

INK = HexColor("#1a1a1a")
MUTED = HexColor("#6b6b6b")
LINE = HexColor("#b5b5b5")
SET_COLORS = {"A": HexColor("#2f5d8a"), "B": HexColor("#7a3f8a"),
              "C": HexColor("#a2552a"), "D": HexColor("#2e7a4f")}
SET_NAMES = {"A": "Argument basics", "B": "Validity, strength & first fallacies",
             "C": "Informal fallacies, part 1", "D": "Informal fallacies, part 2 & biases"}

# (set, front prompt, answer title, answer body, check-course flag)
CARDS = [
 ("A", "What is the difference between an <b>opinion</b> and a <b>philosophical argument</b>?",
  "Opinion vs. philosophical argument",
  "An <b>opinion</b> is a claim stated without support. A <b>philosophical argument</b> gives reasons (premises) meant to support a claim (conclusion), so it can be checked and judged.<br/><br/><i>\"Lying is wrong\"</i> is an opinion. Adding <i>why</i> it is wrong turns it into an argument.", False),
 ("A", "Name the <b>two parts</b> of every argument and say what each one does.",
  "Premises and conclusion",
  "<b>Premises</b>: the statements offered as reasons or evidence.<br/><b>Conclusion</b>: the claim the premises are meant to support.<br/><br/><i>All humans are mortal. Socrates is human.</i> (premises) <i>So Socrates is mortal.</i> (conclusion)", False),
 ("A", "List three <b>premise indicators</b> and three <b>conclusion indicators</b>.",
  "Indicator words",
  "<b>Premise indicators</b>: because, since, given that, for, as shown by, the reason is.<br/><br/><b>Conclusion indicators</b>: therefore, thus, so, hence, consequently, it follows that.<br/><br/>They are clues, not guarantees. Always check the role each sentence plays.", False),
 ("A", "What is the difference between <b>truth value analysis</b> and <b>logical analysis</b> of an argument?",
  "Truth value vs. logical analysis",
  "<b>Truth value analysis</b> asks: are the premises actually true?<br/><br/><b>Logical analysis</b> asks: <i>if</i> the premises were true, would the conclusion follow?<br/><br/>A good argument passes both tests.", False),
 ("A", "\"The pavement is wet <b>because</b> it rained last night.\"<br/><br/>Is this an <b>argument</b> or an <b>explanation</b>? How can you tell?",
  "Argument vs. explanation",
  "<b>Explanation.</b> Nobody doubts that the pavement is wet; the sentence says <i>why</i> it is.<br/><br/>An <b>argument</b> tries to show <i>that</i> a claim is true. An <b>explanation</b> says <i>why or how</i> something already accepted is true. \"Because\" can appear in both.", False),
 ("A", "What is the difference between a <b>deductive</b> and an <b>inductive</b> argument?",
  "Deductive vs. inductive",
  "<b>Deductive</b>: claims the conclusion follows <i>necessarily</i>. If the premises are true, the conclusion must be true.<br/><br/><b>Inductive</b>: claims the conclusion is <i>probably</i> true given the premises.<br/><br/><i>Every swan I have seen is white, so the next one will be</i> is inductive.", False),

 ("B", "What is the difference between a <b>valid</b> and a <b>sound</b> argument?",
  "Valid vs. sound",
  "<b>Valid</b>: it is impossible for the premises to be true and the conclusion false. This is about form, not actual truth.<br/><br/><b>Sound</b>: valid <i>and</i> every premise is actually true.<br/><br/>A valid argument can have false premises. A sound argument cannot.", False),
 ("B", "How does the <b>counterexample method</b> show that an argument is invalid?",
  "Counterexample method",
  "Build an argument with the <b>same form</b> where the premises are clearly true and the conclusion is clearly false. If that can happen, the form is invalid.<br/><br/><i>All cats are animals. All dogs are animals. So all cats are dogs.</i>", False),
 ("B", "What is the difference between a <b>strong</b> and a <b>cogent</b> inductive argument?",
  "Strong vs. cogent",
  "<b>Strong</b>: if the premises were true, the conclusion would probably be true.<br/><br/><b>Cogent</b>: strong <i>and</i> the premises are actually true, with no key evidence left out.<br/><br/>Strong/cogent is the inductive version of valid/sound.", False),
 ("B", "What is an <b>enthymeme</b>, and what does the <b>principle of charity</b> tell you to do with one?",
  "Enthymeme and principle of charity",
  "<b>Enthymeme</b>: an argument with an unstated premise (or conclusion).<br/><br/><b>Principle of charity</b>: rebuild other people's arguments in their strongest, most reasonable form, filling gaps with the most plausible missing premise.<br/><br/><i>\"He's a lawyer, so he's good at arguing\"</i> assumes lawyers are good at arguing.", False),
 ("B", "What is the difference between a <b>formal</b> and an <b>informal</b> fallacy?",
  "Formal vs. informal fallacies",
  "<b>Formal</b>: an error in the argument's <i>structure</i>, so you can spot it from the form alone (e.g. affirming the consequent: if P then Q; Q; so P).<br/><br/><b>Informal</b>: an error in the <i>content</i>, such as irrelevant reasons, weak evidence or hidden assumptions. You have to look at what is said.", False),
 ("B", "<b>Name the fallacy.</b><br/><br/>\"Don't listen to her plan for the city budget. She's been divorced twice.\"",
  "Ad hominem",
  "Attacking the <b>person</b> (their character, circumstances or hypocrisy) instead of their argument.<br/><br/>Her divorces say nothing about whether the budget plan is any good.", False),

 ("C", "<b>Name the fallacy.</b><br/><br/>\"I met two people from that town and both were rude. Everyone there must be rude.\"",
  "Hasty generalization",
  "Drawing a general conclusion from a sample that is <b>too small or unrepresentative</b>.<br/><br/>Two people cannot represent a whole town.", False),
 ("C", "<b>Name the fallacy.</b><br/><br/>\"If we let students retake one test, soon they'll want to retake every test, and then grades will mean nothing.\"",
  "Slippery slope",
  "Claiming one step will lead through a <b>chain of events</b> to an extreme outcome, with no good reason to think each link will actually happen.", False),
 ("C", "<b>Name the fallacy.</b><br/><br/>\"This news source is trustworthy because it never reports anything false.\"",
  "Begging the question",
  "The premises <b>assume the conclusion</b> they are meant to prove (circular reasoning). Whether it never reports anything false is exactly the question.<br/><br/><i>Check this definition against your course materials.</i>", True),
 ("C", "<b>Name the fallacy.</b><br/><br/>\"A famous actor says this diet cures diabetes, so it must work.\"",
  "Appeal to (unqualified) authority",
  "Treating someone's word as proof when they are <b>not an expert</b> on the topic (or when experts disagree).<br/><br/>Citing a relevant expert consensus is <i>not</i> a fallacy.", False),
 ("C", "<b>Name the fallacy.</b><br/><br/>\"No one has ever proven ghosts don't exist, so they must be real.\"",
  "Appeal to ignorance",
  "Concluding a claim is true because it has not been <b>proven false</b> (or false because it has not been proven true). A lack of evidence is not evidence.", False),
 ("C", "<b>Name the fallacy.</b><br/><br/>\"Either you support this law, or you don't care about children's safety.\"",
  "False dichotomy",
  "Presenting <b>only two options</b> when others exist. You could care about safety and still think this law is a bad way to get it.", False),

 ("D", "<b>Name the fallacy.</b><br/><br/>A: \"We should cut the military budget a bit.\"<br/>B: \"So you want to leave the country defenceless?\"",
  "Straw man",
  "<b>Misrepresenting</b> an opponent's position as a weaker or more extreme version, then attacking that version instead of the real one.", False),
 ("D", "<b>Name the fallacy.</b><br/><br/>\"Herbal remedies are natural, so they must be better for you than medicine.\"",
  "Naturalistic fallacy",
  "Concluding that something is good or right <b>because it is natural</b>, or more broadly deriving an \"ought\" from an \"is\".<br/><br/><i>Check this definition against your course materials, since courses frame it differently.</i>", True),
 ("D", "<b>Name the fallacy.</b><br/><br/>\"Employees are like nails. Nails have to be hit on the head to work, so employees do too.\"",
  "False analogy",
  "Arguing that two things alike in some ways must be alike in another, when the <b>similarities are irrelevant</b> or the differences matter.<br/><br/><i>Check this definition against your course materials.</i>", True),
 ("D", "Name the <b>bias</b>: someone sure a stock will rise reads only the bullish news and dismisses every warning.",
  "Confirmation bias",
  "The tendency to <b>seek out, notice and remember</b> evidence that supports what we already believe, and to ignore or discount evidence against it.", False),
 ("D", "Name the <b>bias</b>: after watching news about a plane crash, someone decides flying is more dangerous than driving.",
  "Availability error",
  "Judging how likely or common something is by <b>how easily examples come to mind</b>. Vivid or recent events feel more frequent than they are.", False),
 ("D", "Name the <b>effect</b>: people with the least skill at a task are often the most confident they are good at it.",
  "Dunning-Kruger effect",
  "People with <b>low ability</b> in an area tend to <b>overestimate</b> their competence, partly because they lack the skill to see their own mistakes.", False),
]

QUIZ = [
 ("\"My uncle smoked all his life and lived to 95, so smoking can't be that bad.\"", "Hasty generalization"),
 ("\"You can't trust his argument about climate policy; he drives an SUV.\"", "Ad hominem (tu quoque / hypocrisy)"),
 ("\"Nobody has shown this supplement is harmful, so it's safe.\"", "Appeal to ignorance"),
 ("\"We either ban phones in class entirely or accept that no one will learn.\"", "False dichotomy"),
 ("\"Free will exists, because we are free to choose what we do.\"", "Begging the question"),
 ("Feminists want equal pay. Critic: \"They want to make men second-class citizens.\"", "Straw man"),
 ("\"If we allow food in the library, next it'll be parties, then it'll be trashed.\"", "Slippery slope"),
 ("\"A Nobel-winning physicist says this vaccine is unsafe, so it is.\"", "Appeal to authority (outside their field)"),
 ("\"The universe is like a watch. Watches have makers, so the universe does too.\"", "False analogy (check against your course)"),
 ("\"Animals eat meat in nature, so eating meat must be morally right.\"", "Naturalistic fallacy"),
 ("All birds can fly. Penguins are birds. So penguins can fly. Valid? Sound?", "Valid but not sound (premise 1 is false)"),
 ("If it rains, the ground is wet. The ground is wet. So it rained. Valid?", "Invalid: affirming the consequent (a formal fallacy)"),
]

W, H = letter
M = 36
COLS, ROWS = 2, 3
CW, CH = (W - 2 * M) / COLS, (H - 2 * M - 20) / ROWS

front_style = ParagraphStyle("front", fontName="Helvetica", fontSize=12.5, leading=17, textColor=INK, alignment=1)
title_style = ParagraphStyle("atitle", fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=INK, spaceAfter=6)
body_style = ParagraphStyle("abody", fontName="Helvetica", fontSize=9.6, leading=12.6, textColor=INK)


def card_origin(col, row):
    return M + col * CW, H - M - 20 - (row + 1) * CH


def cut_lines(c):
    c.setStrokeColor(LINE)
    c.setDash(4, 3)
    c.setLineWidth(0.6)
    for i in range(COLS + 1):
        x = M + i * CW
        c.line(x, M, x, H - M - 20)
    for j in range(ROWS + 1):
        y = H - M - 20 - j * CH
        c.line(M, y, W - M, y)
    c.setDash()


def header(c, text, sub):
    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(INK)
    c.drawString(M, H - M, text)
    c.setFont("Helvetica", 8.5)
    c.setFillColor(MUTED)
    c.drawRightString(W - M, H - M, sub)


def tag(c, x, y, s, label):
    c.setFillColor(SET_COLORS[s])
    c.rect(x + 10, y + CH - 26, 64, 15, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(x + 42, y + CH - 21.5, label)


def fit(paras, w, h):
    return KeepInFrame(w, h, paras, mode="shrink")


def draw_front(c, idx, card, col, row):
    s, prompt = card[0], card[1]
    x, y = card_origin(col, row)
    tag(c, x, y, s, f"SET {s}  #{idx}")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7.5)
    c.drawRightString(x + CW - 10, y + CH - 22, "answer before you flip")
    f = Frame(x + 18, y + 14, CW - 36, CH - 52, showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    p = Paragraph(prompt, front_style)
    _, ph = p.wrap(CW - 36, CH - 52)
    pad = max(0, (CH - 52 - ph) / 2)
    from reportlab.platypus import Spacer
    f.addFromList([Spacer(1, pad), fit([p], CW - 36, CH - 52 - pad)], c)


def draw_back(c, idx, card, col, row):
    s, _, title, body, flag = card
    x, y = card_origin(col, row)
    tag(c, x, y, s, f"#{idx} ANSWER")
    f = Frame(x + 14, y + 10, CW - 28, CH - 44, showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    f.addFromList([fit([Paragraph(title, title_style), Paragraph(body, body_style)], CW - 28, CH - 44)], c)


def schedule_page(c):
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(M, H - M - 14, "Arguments, Logic & Fallacies")
    c.setFont("Helvetica", 11)
    c.setFillColor(MUTED)
    c.drawString(M, H - M - 32, "24 practice flashcards in four sets, a spaced-review schedule and a mixed practice quiz")

    y = H - M - 66
    for s in "ABCD":
        c.setFillColor(SET_COLORS[s])
        c.rect(M, y - 3, 10, 10, stroke=0, fill=1)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold", 10.5)
        c.drawString(M + 16, y, f"Set {s}: {SET_NAMES[s]}")
        c.setFont("Helvetica", 9)
        c.setFillColor(MUTED)
        nums = [i + 1 for i, k in enumerate(CARDS) if k[0] == s]
        c.drawString(M + 280, y, f"cards {nums[0]}-{nums[-1]}")
        y -= 17

    y -= 12
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(M, y, "Schedule")
    c.setFont("Helvetica", 9)
    c.setFillColor(MUTED)
    c.drawString(M + 70, y, "Each set is reviewed 1, 3, 7 and 14 days after you learn it. Tick each box when done.")
    y -= 20
    rows = [(1, "Learn Set A", 6), (2, "Learn Set B, review Set A", 12), (3, "Learn Set C, review Set B", 12),
            (4, "Learn Set D, review Sets A and C", 18), (5, "Review Sets B and D", 12), (6, "Review Set C", 6),
            (7, "Review Set D", 6), (8, "Review Set A", 6), (9, "Review Set B", 6), (10, "Review Set C", 6),
            (11, "Review Set D", 6), (15, "Final review: Set A", 6), (16, "Final review: Set B", 6),
            (17, "Final review: Set C", 6), (18, "Final review: Set D", 6)]
    c.setFont("Helvetica-Bold", 9)
    c.drawString(M + 4, y, "DAY")
    c.drawString(M + 50, y, "TASK")
    c.drawString(M + 330, y, "CARDS")
    c.drawString(M + 400, y, "DATE")
    c.drawString(M + 490, y, "DONE")
    y -= 6
    for d, task, n in rows:
        c.setStrokeColor(LINE)
        c.setLineWidth(0.5)
        c.line(M, y, W - M, y)
        y -= 16
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold" if d == 4 else "Helvetica", 10)
        c.drawString(M + 4, y + 4, str(d))
        c.drawString(M + 50, y + 4, task)
        c.drawString(M + 330, y + 4, str(n))
        c.setStrokeColor(LINE)
        c.line(M + 400, y + 2, M + 470, y + 2)
        c.setStrokeColor(INK)
        c.rect(M + 496, y + 1, 11, 11, stroke=1, fill=0)
    c.setStrokeColor(LINE)
    c.line(M, y - 2, W - M, y - 2)

    y -= 30
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(M, y, "How to use it")
    tips = [
        "<b>Answer first.</b> Say or write your answer before flipping the card. Recalling it is what builds memory, more than rereading.",
        "<b>Missed cards restart.</b> If you get a card wrong, treat it as new and restart its intervals.",
        "<b>Keep sessions short.</b> Most days have 6-12 cards (about 10-15 minutes). Day 4 is the heavy day, with 18 cards, so allow about 20 minutes.",
        "<b>Check module-specific cards.</b> Cards 15 (begging the question), 20 (naturalistic fallacy) and 21 (false analogy) should be checked against your course materials.",
        "<b>Printing.</b> Print double-sided, <b>flip on long edge</b>, then cut along the dashed lines. Each answer lands on the back of its question.",
    ]
    tip_style = ParagraphStyle("tip", fontName="Helvetica", fontSize=9.6, leading=13, textColor=INK, bulletIndent=0, leftIndent=12)
    f = Frame(M, M, W - 2 * M, y - M - 6, showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    f.addFromList([Paragraph(t, tip_style, bulletText="-") for t in tips], c)


def quiz_pages(c):
    from reportlab.platypus import Spacer
    q_style = ParagraphStyle("q", fontName="Helvetica", fontSize=11, leading=15, textColor=INK, leftIndent=22, firstLineIndent=-22)
    blank = ParagraphStyle("blank", fontName="Helvetica", fontSize=9, leading=12, textColor=MUTED, leftIndent=22)
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(M, H - M - 14, "Mixed practice quiz")
    c.setFont("Helvetica", 10)
    c.setFillColor(MUTED)
    c.drawString(M, H - M - 30, "Use after Day 11. Name the fallacy or bias, or judge the argument. Answer key on the next page.")
    story = []
    for i, (q, _) in enumerate(QUIZ, 1):
        story += [Paragraph(f"<b>{i}.</b>&nbsp;&nbsp;{q}", q_style),
                  Paragraph("Answer: ______________________________________________", blank), Spacer(1, 12)]
    Frame(M, M, W - 2 * M, H - 2 * M - 46, showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0).addFromList(story, c)
    c.showPage()

    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(M, H - M - 14, "Answer key")
    story = [Paragraph(f"<b>{i}.</b>&nbsp;&nbsp;{a}", q_style) for i, (_, a) in enumerate(QUIZ, 1)]
    story = [x for p in story for x in (p, Spacer(1, 8))]
    story.append(Spacer(1, 14))
    story.append(Paragraph("Score 10+ out of 12: you're in good shape. Any you missed: find that card and restart its intervals.",
                           ParagraphStyle("n", fontName="Helvetica-Oblique", fontSize=10, leading=14, textColor=MUTED)))
    Frame(M, M, W - 2 * M, H - 2 * M - 40, showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0).addFromList(story, c)
    c.showPage()


def main(path):
    c = canvas.Canvas(path, pagesize=letter)
    c.setTitle("Arguments, Logic & Fallacies - Practice Flashcards")
    schedule_page(c)
    c.showPage()
    # blank back of the schedule sheet so every card page pairs with its answer page when printed duplex
    c.setFillColor(MUTED)
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(W / 2, H / 2, "Back of the schedule. Left blank so the cards line up when printed double-sided.")
    c.showPage()
    for s in "ABCD":
        items = [(i + 1, k) for i, k in enumerate(CARDS) if k[0] == s]
        header(c, f"Set {s}: {SET_NAMES[s]}  -  QUESTIONS", "print double-sided, flip on long edge, cut on dashed lines")
        cut_lines(c)
        for n, (idx, card) in enumerate(items):
            draw_front(c, idx, card, n % COLS, n // COLS)
        c.showPage()
        header(c, f"Set {s}: {SET_NAMES[s]}  -  ANSWERS", "back of the previous page")
        cut_lines(c)
        for n, (idx, card) in enumerate(items):
            # mirror columns so each answer prints behind its question on a long-edge flip
            draw_back(c, idx, card, COLS - 1 - n % COLS, n // COLS)
        c.showPage()
    quiz_pages(c)
    c.save()


if __name__ == "__main__":
    import os
    main(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logic-flashcards.pdf"))
