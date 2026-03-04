import re

SLANG = {
    "th": "tahun",
    "thn": "tahun",
    "bln": "bulan",
    "hr": "hari",
    "x": "kali",
    "per": "setiap ",

    "emg": "memang",
    "emgnya": "memangnya",
    "pgn": "ingin",
    "pngen": "ingin",
    "pengen": "ingin",
    "bole": "boleh",
    "bolehga": "boleh tidak",
    "bolehgk": "boleh tidak",
    "bolegk": "boleh tidak",
    "perbenang": "per benang",

    "ak": "aku",
    "ad": "ada",
    "gaada": "tidak ada",
    "gada": "tidak ada",
    "ka": "kak",
    "gk": "gak",
    "ga": "gak",
    "gx": "gak",
    "g": "gak",
    "tdk": "tidak",
    "dgn": "dengan",
    "utk": "untuk",
    "yg": "yang",
    "dpt": "dapat",
    "bs": "bisa",
    "bsa": "bisa",
    "blm": "belum",
    "sdh": "sudah",
    "udh": "sudah",
    "udah": "sudah",
    "gmn": "gimana",
    "gmna": "gimana",
    "gimana": "bagaimana",
    "kyk": "kayak",
    "klo": "kalau",
    "kl": "kalau",
    "kalo": "kalau",
    "krn": "karena",
    "krna": "karena",
    "tp": "tapi",
    "trs": "terus",
    "trus": "terus",
    "bgt": "banget",
    "bngt": "banget",
    "sm": "sama",
    "sma": "sama",
    "org": "orang",
    "jg": "juga",
    "jga": "juga",
    "ap" : "apa",
    "aja": "saja",
    "doang": "saja",
    "aj": "saja",
    "lg": "lagi",
    "lgi": "lagi",
    "skrg": "sekarang",
    "skg": "sekarang",
    "hrs": "harus",
    "jd": "jadi",
    "jdi": "jadi",
    "dl": "dulu",
    "dlu": "dulu",
    "mksd": "maksud",
    "mksud": "maksud",
    "brp": "berapa",
    "brpa": "berapa",
    "dmn": "dimana",
    "dmna": "dimana",
    "knp": "kenapa",
    "kpn": "kapan",
    "kpan": "kapan",
    "plg": "paling",
    "min": "minimal",
    "max": "maksimal",
    "maks": "maksimal",
    
    "treatmen": "treatment",
    "treatmnt": "treatment",
    "treatement": "treatment",
    "botok": "botox",
    "botoks": "botox",
    "fller": "filler",
    "flier": "filler",
    "filller": "filler",
    "facila": "facial",
    "fasial": "facial",
    "lazer": "laser",
    "laseer": "laser",
    "benag": "benang",
    "bnang": "benang",
    "tanam": "tarik",  #tanam benang = tarik benang
    
    "bekasih": "bekasi",
    "bksi": "bekasi",
    "summarecon": "bekasi",
    "kemank": "kemang",
    "kmang": "kemang",
    "tanggerang": "tangerang",
    "tgerang": "tangerang",
    "serpong": "tangerang",
    "bandumg": "bandung",
    "bdg": "bandung",
    "pku": "pekanbaru",
}

def normalize_slang(text: str) -> str: #the input is in str and output in str
    words = text.lower().split() #convert the string to a list of words
    normalized = [] #will consist list of normalized word

    for word in words: #to clean the words first from punctuation then check to dictionary
        clean_word = re.sub(r'[!,?.]', '', word) #re.sub(char wanted to be replaced, result char after replaced, the string to modify)

        if clean_word in SLANG:
            normalized.append(SLANG[clean_word])
        else:
            normalized.append(word)
    
    return ' '.join(normalized) #return the full string after normalized

def preprocess_query(query:str) -> str: 
    query = query.lower() #double .lower() for safety if we ever call this function not through function above
    query = normalize_slang(query)
    query = ' '.join(query.split()) #to erase more than one space within words
    return query

if __name__ == "__main__": #to test the code on this file
    test = [
        "bekasih ada gk kak",
        "brp harga botok",
        "bs cicilan  ga",
        "treatmen facila    ada ap aj",
        "dmn alamat kemank",
    ]
    for q in test:
        print(f"Original: {q}")
        print(f"Processed: {preprocess_query(q)}")
        print()