from logging import NullHandler
from requests import api
import telebot
from telebot import types
import requests
import os
import json
app=Telebot(os.environ['TELEGRAM_TOKEN'])
main_markup = types.ReplyKeyboardMarkup(row_width=3)
main_markup.add(types.KeyboardButton("Carátula"), types.KeyboardButton(
    "Notas"), types.KeyboardButton("Ayuda"))
api_url="http://generador-caratulas-ucsp-api.herokuapp.com"
carreras = [
    "ARQUITECTURA Y URBANISMO",
    "INGENIERÍA AMBIENTAL",
    "INGENIERIA MECATRÓNICA",
    "ADMINISTRACIÓN DE NEGOCIOS",
    "INGENIERÍA CIVIL",
    "CONTABILIDAD",
    "CIENCIA DE LA COMPUTACIÓN",
    "DERECHO",
    "EDUCACIÓN INICIAL Y PRIMARIA",
    "INGENIERÍA ELECTRÓNICA Y DE TELECOMUNICACIONES",
    "INGENIERÍA INDUSTRIAL",
    "PSICOLOGÍA"
]
carreras_markup=types.ReplyKeyboardMarkup(row_width=3)
for carrera in carreras:
    carreras_markup.add(types.KeyboardButton(carrera))
semestre_markup=types.ReplyKeyboardMarkup(row_width=3)
for i in range(1,11):
    semestre_markup.add(types.KeyboardButton(str(i)))
@app.message_handler(commands=["start"])
def start(message):
    app.send_message(
        message.chat.id, "¡Hola! Bienvenido al bot (no-oficial) de la UCSP, por favor selecciona una opción.", reply_markup=main_markup)
@app.message_handler(content_types=['text'])
def flujo_principal(message):
    if message.text == "Carátula":
        app.send_message(
            message.chat.id, "¿Cual es tu carrera?",reply_markup=carreras_markup)
        app.register_next_step_handler(message, titulo)
    elif message.text == "Notas":
        app.send_message(
            message.chat.id, "¡Esta función aún está en construcción!", reply_markup=main_markup)
def titulo(message):
    app.send_message(message.chat.id, "¿Cual es el título de tu trabajo?",reply_markup=types.ReplyKeyboardRemove())
    app.register_next_step_handler(message,curso,message.text)
def curso(message,carrera):
    app.send_message(message.chat.id, "¿Cual es el curso?")
    app.register_next_step_handler(message,sems, carrera,message.text)
def sems(message,carrera,titulo):
    app.send_message(message.chat.id, "¿Cual es el semestre?",reply_markup=semestre_markup)
    app.register_next_step_handler(message,alumnos, carrera,titulo,message.text)
def alumnos(message,carrera,titulo,curso):
    app.send_message(message.chat.id, "Escriba los nombres de los alumnos porfavor, separados por comas.\n\nNo se admiten más de 6 ni menos 1 alumnos.",reply_markup=types.ReplyKeyboardRemove())
    app.register_next_step_handler(message,generar_pdf,carrera,titulo,curso,message.text)
def generar_pdf(message,carrera,titulo,curso,semestre):
    alumnos=message.text.split(",")
    alumnos=list(map(str.strip,alumnos))
    if len(alumnos) > 6 or not alumnos:
        app.send_message(message.chat.id, "No se admiten más de 6 alumnos.")
    else:
        data={"carrera":carrera,"titulo":titulo,"curso":curso,"semestre":int(semestre),"alumnos":alumnos}
        r=requests.post(api_url,data=json.dumps(data))
        #If this doesn't work I'll have to save the pdf in a file
        #and send it to the user
        app.send_document(message.chat.id,api_url+"retornar_caratula/"+r.text)
        


if __name__ == '__main__':
    app.polling(none_stop=True)