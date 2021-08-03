import telebot,requests,os,json,redis,random,string
from telebot import types
from scrap_academico import get_notas_string
from PyPDF2 import PdfFileMerger
# Here's where markups are declared
main_markup = types.ReplyKeyboardMarkup(row_width=3)
main_markup.add(types.KeyboardButton("/caratula"), types.KeyboardButton(
    "/notas"), types.KeyboardButton("/ayuda"))
yes_no_markup = types.ReplyKeyboardMarkup(row_width=2)
yes_no_markup.add(types.KeyboardButton("Si"), types.KeyboardButton(
    "No"), types.KeyboardButton("Nunca"))
yesno_markup=types.ReplyKeyboardMarkup(row_width=2)
yesno_markup.add(types.KeyboardButton("Si"), types.KeyboardButton(
    "No"))
#####################################################################
# Static variables
app=telebot.TeleBot(os.environ['TELEGRAM_TOKEN'])
api_url = "http://generador-caratulas-ucsp-api.herokuapp.com/"
redis = redis.Redis.from_url(os.environ['REDIS_URL'])
#Lo cambié todo a minúsculas porque al parser de json no le agrada :C
#TODO: Somehow parse the special characters e.g (INGENIERÍA)
carreras = [
    "ARQUITECTURA Y URBANISMO",
    "INGENIERIA AMBIENTAL",
    "INGENIERIA MECATRONICA",
    "ADMINISTRACION DE NEGOCIOS",
    "INGENIERIA CIVIL",
    "CONTABILIDAD",
    "CIENCIA DE LA COMPUTACION",
    "DERECHO",
    "EDUCACION INICIAL Y PRIMARIA",
    "INGENIERIA ELECTRONICA Y DE TELECOMUNICACIONES",
    "INGENIERIA INDUSTRIAL",
    "PSICOLOGIA"
]
carreras_markup = types.ReplyKeyboardMarkup(row_width=3)
for carrera in carreras:
    carreras_markup.add(types.KeyboardButton(carrera))
semestre_markup = types.ReplyKeyboardMarkup(row_width=3)
for i in range(1, 11):
    semestre_markup.add(types.KeyboardButton(str(i)))

@app.message_handler(commands=["start"])
def start(message):
    app.send_message(
        message.chat.id, "¡Hola! Bienvenido al bot (no-oficial) de la UCSP, por favor selecciona una opción.", reply_markup=main_markup)


@app.message_handler(commands=['caratula'])
def cara(message):
    app.send_message(
        message.chat.id, "¿Cual es tu carrera?", reply_markup=carreras_markup)
    app.register_next_step_handler(message, titulo)


def titulo(message):
    app.send_message(message.chat.id, "¿Cual es el título de tu trabajo?",
                     reply_markup=types.ReplyKeyboardRemove())
    app.register_next_step_handler(message, curso, message.text)


def curso(message, carrera):
    app.send_message(message.chat.id, "¿Cual es el curso?")
    app.register_next_step_handler(message, sems, carrera, message.text)


def sems(message, carrera, titulo):
    app.send_message(message.chat.id, "¿Cual es el semestre?",
                     reply_markup=semestre_markup)
    app.register_next_step_handler(
        message, alumnos, carrera, titulo, message.text)


def alumnos(message, carrera, titulo, curso):
    app.send_message(message.chat.id, "Escriba los nombres de los alumnos porfavor, separados por comas.\n\nNo se admiten más de 6 ni menos 1 alumnos.",
                     reply_markup=types.ReplyKeyboardRemove())
    app.register_next_step_handler(
        message, generar_pdf, carrera, titulo, curso, message.text)


def generar_pdf(message, carrera, titulo, curso, semestre):
    alumnos = message.text.split(",")
    alumnos = list(map(str.strip, alumnos))
    if len(alumnos) > 6 or not alumnos:
        app.send_message(message.chat.id, "No se admiten más de 6 alumnos.")
    else:
        data = {"carrera": carrera, "titulo": titulo, "curso": curso,
                "semestre": int(semestre), "alumnos": alumnos}
        try:
            r = requests.post(api_url, data=json.dumps(data))
            sent=app.send_document(message.chat.id, api_url +
                              "retornar_caratula/"+r.text,reply_markup=main_markup)
            redis.hset(message.chat.id, "last_pdf", sent.document.file_id)
        except Exception as e:
            print(e)
            app.send_message(
                message.chat.id, "Hubo un problema al intentar generar la carátula.", reply_markup=main_markup)


@app.message_handler(commands=['notas'])
def pri_not(message):
    cod=redis.hget(message.chat.id, "codigo")
    psw=redis.hget(message.chat.id, "password")
    if cod and psw:
        to_edit=app.send_message(message.chat.id, "Un momento por favor :)").message_id
        try:
            grades,kind = get_notas_string(cod, psw)
            if kind==0:
                app.delete_message(message.chat.id, to_edit)
                app.send_photo(message.chat.id, grades, reply_markup=main_markup)
            else:
                app.delete_message(message.chat.id, to_edit)
                app.send_message(message.chat.id, grades, reply_markup=main_markup)
        except Exception as e:
            print(e)
            app.delete_message(message.chat.id, to_edit)
            app.send_message(message.chat.id, "Hubo un error al intentar obtener las notas.",reply_markup=main_markup)
    else:
        app.send_message(
        message.chat.id, "Ingrese su código de alumno.", reply_markup=types.ReplyKeyboardRemove())
        app.register_next_step_handler(message, notas)


def notas(message):
    app.send_message(message.chat.id, "Ingrese su contraseña.")
    app.register_next_step_handler(message, notas2, message.text)


def notas2(message, codigo):
    try:
        to_del=app.send_message(message.chat.id, "Un momento por favor :)",reply_markup=types.ReplyKeyboardRemove()).message_id
        grades,kind = get_notas_string(codigo, message.text)
        if kind==0:
            app.delete_message(message.chat.id, to_del)
            app.send_photo(message.chat.id, grades, reply_markup=main_markup)
        else:
            app.delete_message(message.chat.id, to_del)
            app.send_message(message.chat.id, grades, reply_markup=main_markup)
        if redis.hget(message.chat.id, "nunca")!=True:
            app.send_message(
                message.chat.id, "¿Desea guardar sus credenciales para sólo presionar el botón notas la próxima vez?", reply_markup=yes_no_markup)
            app.register_next_step_handler(
                message, save_creds, codigo, message.text)
    except Exception as e:
        print(e)
        app.delete_message(message.chat.id, to_del)
        app.send_message(
            message.chat.id, "Hubo un problema al intentar obtener las notas.", reply_markup=main_markup)


def save_creds(message, codigo, password):
    if message.text == "Si":
        redis.hset(message.chat.id, 'codigo',codigo)
        redis.hset(message.chat.id, 'password',password)
        app.send_message(
            message.chat.id, "Credenciales guardadas correctamente.", reply_markup=main_markup)
    elif message.text == "Nunca":
        redis.hset(message.chat.id, 'nunca',True)
        app.send_message(message.chat.id, "Okay.", reply_markup=main_markup)


@app.message_handler(commands=['ayuda'])
def ayuda(message):
    app.send_message(
        message.chat.id, "Para usar el bot no oficial de la UCSP usa los siguientes comandos:\n Para generar una carátula, escriba: /caratula e ingrese la información en cuanto se solicite\.\n\nPara obtener las notas de un alumno, escriba: /notas e ingrese su código y contraseña en cuanto se solicite\.\n\nPara obtener ayuda sobre el bot escriba: /ayuda\n\nTambién puedo ponerle la carátula encima a tus trabajos, si lo deseas, envía un documento y le pondré la última carátula generada.\n\n\nSi desea revisar/contribuir el código fuente de este bot puede revisarlo [aquí](https://github.com/rafaelcanoguitton/botUCSP)\.\nSi desea comunicarse con el creador del bot puede hacerlo [aquí](https://t.me/rafxar)\.", reply_markup=main_markup, parse_mode='MarkdownV2', disable_web_page_preview=True)
@app.message_handler(content_types=['document'])
def doc_handler(message):
    app.send_message(message.chat.id, "¿Desea poner como carátula de este documento la última carátula generada?",reply_markup=yesno_markup)
    app.register_next_step_handler(message, set_caratula, message.document.file_id)
def set_caratula(message,doc_id):
    if message.text == "Si":
        fileid=redis.hget(message.chat.id, "last_pdf")
        if fileid:
            try:
                app.send_message(message.chat.id, "Un momento por favor :)",reply_markup=types.ReplyKeyboardRemove())
                cara_info=app.get_file(fileid)
                tarea_info=app.get_file(doc_id)
                cara_file=requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(os.environ['TELEGRAM_TOKEN'], cara_info.file_path))
                tarea_file=requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(os.environ['TELEGRAM_TOKEN'], tarea_info.file_path))
                cara_name=''.join(random.choice(string.ascii_lowercase) for i in range(8))+".pdf"
                tarea_name=''.join(random.choice(string.ascii_lowercase) for i in range(8))+".pdf"
                open(cara_name,'wb').write(cara_file.content)
                open(tarea_name,'wb').write(tarea_file.content)
                merger=PdfFileMerger()
                merger.append(cara_name)
                merger.append(tarea_name)
                merge_name=''.join(random.choice(string.ascii_lowercase) for i in range(8))+".pdf"
                merger.write(merge_name)
                merger.close()
                app.send_document(message.chat.id, open(merge_name,'rb'),reply_markup=main_markup)
            except Exception as e:
                print(e)
                app.send_message(message.chat.id,'Hubo un error al juntar los archivos.',reply_markup=main_markup)
            finally:
                #Inside a try in case some file couldn't be created
                #so it doesn't crash the entire app
                try:
                    os.remove(cara_name)
                    os.remove(tarea_name)
                    os.remove(merge_name)
                except:
                    pass
        else:
            app.send_message(message.chat.id, "Usted no ha generado una carátula aún.")
    elif message.text == "No":
        app.send_message(message.chat.id, "Okay.", reply_markup=main_markup)
if __name__ == '__main__':
    app.polling(none_stop=True,)
