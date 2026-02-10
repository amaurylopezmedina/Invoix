import requests


def consulta_rnc(rnc):
    url = "https://dgii.gov.do/wsMovilDGII/WSMovilDGII.asmx/ValidaRNC_Cedula"

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Origin": "https://dgii.gov.do",
        "Referer": "https://dgii.gov.do/",
    }

    payload = f"Valor={rnc}"

    r = requests.post(url, headers=headers, data=payload, timeout=30)
    print(r.status_code)
    return r.text


print(consulta_rnc("131709745"))
