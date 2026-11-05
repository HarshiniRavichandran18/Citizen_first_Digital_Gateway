import re
from collections import deque, defaultdict

# ---- TREE: question flow (category -> specific question -> state question) ----
class Node:
    def __init__(self, q, options): self.q, self.options = q, options  # options: label -> (keywords, child Node)
STATE = Node("Which state are you applying from? / எந்த மாநிலம்?",
             {"Tamil Nadu / தமிழ்நாடு": ([], None), "Other state / வேறு மாநிலம்": ([], None)})
def _t(q, opts): return Node(q, {k: (v, STATE) for k, v in opts.items()})
TREE = {
 'Education': _t("What is your education level? / கல்வி நிலை?", {"School / பள்ளி": ['school', 'class', 'std'], "College / கல்லூரி": ['college', 'degree', 'higher education', 'graduate'], "Other / மற்றவை": []}),
 'Healthcare': _t("Who needs help? / யாருக்கு உதவி தேவை?", {"Woman / பெண்": ['pregnan', 'delivery', 'women'], "Differently abled / மாற்றுத்திறனாளி": ['differently abled', 'disab'], "Someone else / மற்றவர்": []}),
 'Employment': _t("What do you need? / என்ன தேவை?", {"Start a business / தொழில் தொடங்க": ['entrepreneur', 'enterprise', 'loan', 'business'], "Skill training / திறன் பயிற்சி": ['training', 'skill'], "A job / வேலை": ['employment', 'job']}),
 'Agriculture': _t("Are you a farmer? / நீங்கள் விவசாயியா?", {"Yes / ஆம்": ['farmer', 'agricultur'], "No / இல்லை": []}),
 'Pension': _t("Pension for whom? / யாருக்கு ஓய்வூதியம்?", {"Widow or deserted wife / விதவை": ['widow', 'wives', 'deserted'], "Elderly / முதியோர்": ['old age', 'senior', 'aged'], "Differently abled / மாற்றுத்திறனாளி": ['differently abled'], "Transgender / திருநங்கை": ['transgender']}),
 'Welfare': _t("Who is the help for? / யாருக்கான உதவி?", {"Girl child / பெண் குழந்தை": ['girl'], "Marriage assistance / திருமண உதவி": ['marriage'], "Other / மற்றவை": []}),
}
def walk(cat, answers):
    node, kws = TREE.get(cat), []
    for a in answers:
        if node is None or a not in node.options: return None, kws
        k, node = node.options[a]; kws += k
    return node, kws
def next_question(cat, answers):
    node, _ = walk(cat, answers)
    return {'q': node.q, 'options': list(node.options)} if node else None
def answer_keywords(cat, answers): return walk(cat, answers)[1]

# ---- GRAPH: service <-> document (bipartite adjacency list) ----
DOCS = [(r'aadh?aa?r', 'Aadhaar'), (r'bank', 'Bank details'), (r'community|caste', 'Community certificate'), (r'income', 'Income certificate'),
        (r'photo', 'Passport photo'), (r'\bage\b|birth', 'Age proof'), (r'residen|address|domicile|nativity', 'Residence proof'),
        (r'\bpan\b', 'PAN card'), (r'ration', 'Ration card'), (r'disab', 'Disability certificate'), (r'bonafide|study certificate', 'Bonafide certificate'), (r'mark ?sheet', 'Mark sheet')]
def build_graph(services):
    g = defaultdict(set)
    for s in services:
        for d in s['required_documents']:
            for rx, lbl in DOCS:
                if re.search(rx, d.lower()): g[s['service_id']].add(lbl); g[lbl].add(s['service_id'])
    return g
COMMON = {'Aadhaar', 'Bank details', 'Passport photo'}  # needed by almost everything, so they say nothing about similarity
def related(g, sid, top=4):  # BFS 2 levels: service -> documents -> other services
    shared, q, seen = defaultdict(int), deque([(sid, 0)]), {sid}
    while q:
        n, d = q.popleft()
        if d == 2: continue
        for m in g[n]:
            if m in COMMON: continue
            if d == 1 and m != sid: shared[m] += 1
            if m not in seen: seen.add(m); q.append((m, d + 1))
    return sorted(shared, key=shared.get, reverse=True)[:top]
