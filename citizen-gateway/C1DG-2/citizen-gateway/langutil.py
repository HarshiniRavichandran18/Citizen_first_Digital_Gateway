"""Language detection + Tamil/Tanglish -> English query expansion (used only to improve search; the user's text is never altered)."""
import re
TAMIL = re.compile(r'[\u0B80-\u0BFF]')
# Common Tanglish function/content words. Detection needs >=2 hits (or 1 hit and >=40% of tokens) to avoid false positives on English.
TANGLISH_WORDS = set('''enakku enaku ennaku enna eppadi epdi yeppadi venum vendum venuma irukku iruka irukkum illa illai panna pannanum pannalama panrathu
seiyanum seiyalam eppo yaar yaaru ungalukku unga naan nan en ennoda enga inga anga idhu indha intha adhu antha ethu edhu sollunga sollu solla
padikka padikkum padikira ponnu ponnuku ponnukku payyan magan magal amma appa thatha paati vivasayi vivasayam mudhiyor muthiyor vidhavai
velai vela kaasu panam udhavi uthavi arasu arasangam thittam thitam sertha seruvathu porunthum thevai documents-ah apply-pannu theriyuma
puriyala purila konjam romba nalla seri sari ok-ah mudiyuma mudiyum kidaikkum kidaikuma kedaikkum kedaikuma irundha irundhal'''.split())
# keyword -> English search terms (Tamil script and Tanglish spellings)
EXPAND = {
 'scholarship': 'scholarship education student', 'உதவித்தொகை': 'scholarship assistance', 'உதவி': 'assistance', 'udhavi': 'assistance', 'uthavi': 'assistance',
 'மாணவ': 'student education', 'manavar': 'student education', 'padikka': 'study education student', 'padippu': 'education', 'கல்வி': 'education', 'கல்லூரி': 'college education', 'college': 'college higher education',
 'விவசாய': 'farmer agriculture', 'vivasayi': 'farmer agriculture', 'vivasayam': 'agriculture farmer', 'farmer': 'farmer agriculture',
 'முதியோர்': 'senior citizen old age pension', 'mudhiyor': 'senior citizen old age pension', 'muthiyor': 'senior citizen old age pension', 'senior': 'senior citizen old age pension',
 'ஓய்வூதிய': 'pension', 'oivuthiyam': 'pension', 'pension': 'pension',
 'விதவை': 'widow', 'vidhavai': 'widow', 'பெண்': 'women girl', 'ponnu': 'girl women', 'ponnuku': 'girl women', 'ponnukku': 'girl women',
 'மாற்றுத்திறனாளி': 'differently abled disability', 'maatruthiranali': 'differently abled disability', 'திருமண': 'marriage assistance', 'thirumana': 'marriage assistance',
 'வேலை': 'employment job', 'velai': 'employment job', 'தொழில்': 'business entrepreneur loan', 'thozhil': 'business entrepreneur loan', 'மருத்துவ': 'health medical', 'maruthuvam': 'health medical',
 'ஆவண': 'documents', 'aavanam': 'documents', 'aavanangal': 'documents', 'ஆதார்': 'aadhaar', 'aadhar': 'aadhaar', 'ரேஷன்': 'ration card', 'வருமான': 'income certificate', 'varumana': 'income certificate',
 'சாதி': 'community certificate caste', 'jathi': 'community certificate caste', 'jaadhi': 'community certificate caste',
}
# follow-up intents about the scheme currently being discussed
FOLLOW = {
 'eligibility': ['eligib', 'தகுதி', 'thaguthi', 'yaarukku', 'who can', 'arhata', 'porunthum', 'qualif'],
 'documents': ['document', 'ஆவண', 'aavanam', 'aavanangal', 'certificate', 'proof', 'என்ன வேண்டும்', 'enna venum', 'venum'],
 'steps': ['how to apply', 'apply', 'steps', 'procedure', 'விண்ணப்ப', 'vinnappi', 'eppadi', 'epdi', 'process', 'panna'],
 'link': ['link', 'website', 'portal', 'url', 'இணையதள', 'official'],
}
def detect(text):
    """Return 'ta' (Tamil script), 'tanglish' or 'en'."""
    if not text: return 'en'
    letters = [c for c in text if c.isalpha()]
    if letters and sum(bool(TAMIL.match(c)) for c in letters) / len(letters) > .25: return 'ta'
    toks = re.findall(r"[a-z]+", text.lower()); hits = sum(t in TANGLISH_WORDS for t in toks)
    return 'tanglish' if toks and (hits >= 2 or (hits == 1 and hits / len(toks) >= .4)) else 'en'
def expand(q):
    low = q.lower(); extra = [v for k, v in EXPAND.items() if k in low]
    return (q + ' ' + ' '.join(extra)).strip() if extra else q
def follow_intent(q):
    low = q.lower()
    for k, ws in FOLLOW.items():
        if any(w in low for w in ws): return k
    return None
