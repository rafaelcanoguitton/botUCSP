import requests
from bs4 import BeautifulSoup
def get_notas_string(codigo_alumno,contrasenia):
    r_obj = requests.Session()
    url = "https://academico.ucsp.edu.pe/login.aspx"
    fr_soup = r_obj.get(url)
    soup = BeautifulSoup(fr_soup.content, "lxml")
    l = soup.find_all("input", type="hidden")
    data = {
    l[0]['name']: l[0]['value'],
    l[1]['name']: l[1]['value'],
    'txt_usr': codigo_alumno,
    'txt_pwd': contrasenia,
    'btn_ingresar': 'Ingresar',
    'HiddenValueToken': ''}
    r_obj.post(url, verify=False, data=data)
#For some reason if I don't do these get requests the scrapping does not work
    r_obj.get("https://academico.ucsp.edu.pe/menu.aspx")
    r_obj.get("https://academico.ucsp.edu.pe/cabecera.aspx")
    r_obj.get("https://academico.ucsp.edu.pe/inicio.aspx")
    r_obj.get("https://academico.ucsp.edu.pe/menu_opciones.aspx?men_cod=1&men_nom=Alumno")
    r_obj.get("https://academico.ucsp.edu.pe/menu.aspx?OpcNum=7")
#############################################################################
    fr_soup=r_obj.get("https://academico.ucsp.edu.pe/evaluaciones_alumno.aspx")
    soup = BeautifulSoup(fr_soup.content, "lxml")
    l = soup.find_all("input", type="hidden")
    data2={
     '__EVENTTARGET':	"dtg_fichas",
    '__EVENTARGUMENT':	"Select$0",
    '__LASTFOCUS':	"",
     l[0]['name']: l[0]['value'],
     l[1]['name']: l[1]['value'],
    'cmb_periodo':	"125", 
}
    final = r_obj.post('https://academico.ucsp.edu.pe/evaluaciones_alumno.aspx',data=data2)
    sopa_final=BeautifulSoup(final.text, "lxml")
    tabla=[]
    #Yes I build a list of lists, I could have done it without it
    #but it wouldn't work. Since it's such a small dataset I'll leave it like this
    for table in sopa_final.find_all("table", id="dtg_notas"):
        hd=[]
        for header in table.find_all("th"):
            hd.append(header.text)
        hd.pop(0)
        tabla.append(hd)
        for row in table.find_all("tr"):
            notitas=[]
            for cell in row.find_all("td"):
                notitas.append(cell.text)
            if notitas:
                notitas.pop(0)
                tabla.append(notitas)
    mensaje_retorno=""
    for a in range(1,len(tabla)):
        for b,v in enumerate(tabla[a]):
            if v!="-" and b!=2 and b!=1:
                if b==0:
                    mensaje_retorno+=v+" "+tabla[a][b+1]+'\n'
                if b>2:
                    mensaje_retorno+=tabla[0][b]+": "+'\t'+v+'\n'
    return mensaje_retorno