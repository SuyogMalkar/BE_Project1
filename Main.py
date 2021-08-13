import tkinter as tk
import tkinter.font as font
from tkinter import filedialog
import time
import datetime
import speech_recognition as sr 
import os 
from pydub import AudioSegment
from pydub.silence import split_on_silence
import threading
import pyaudio
import wave
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from cryptography.fernet import Fernet

r = sr.Recognizer()

class Test():
    chunk = 1024 
    sample_format = pyaudio.paInt16 
    channels = 2
    fs = 44100
    frames = []
    filename ="RecordingAudio"
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Recording')
        self.isrecording = False

        self.root['bg']='#272358'
        self.w=800
        self.h=400
        self.scn_width = root.winfo_screenwidth()
        self.scn_height = root.winfo_screenheight()
        self.x = (self.scn_width / 2) - (self.w / 2)
        self.y = (self.scn_height / 2) - (self.h / 2)
    
        self.root.geometry(f'{self.w}x{self.h}+{int(self.x)}+{int(self.y)}')

        
        self.button1 = tk.Button(self.root, text='Start',bd=5, bg='white', fg='#272358', font=('times',13,'bold'),width=20,command=self.startrecording)
        self.button2 = tk.Button(self.root, text='Stop',bd=5, bg='white', fg='#272358', font=('times',13,'bold'),width=20,command=self.stoprecording)
      
        self.button1.place(x=300, y=100)
    
        self.button2.place(x=300, y=200)
       
        self.root.mainloop()

    def startrecording(self):
        self.p = pyaudio.PyAudio()  
        self.stream = self.p.open(format=self.sample_format,channels=self.channels,rate=self.fs,frames_per_buffer=self.chunk,input=True)
        self.isrecording = True
        
        print('Recording')
        t = threading.Thread(target=self.record)
        t.start()

    def stoprecording(self):
        self.isrecording = False
        self.root.destroy()
        print('recording complete')
        #self.filename=input('the filename?')
        self.filename = self.filename+".wav"
        wf = wave.open(self.filename, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(self.sample_format))
        wf.setframerate(self.fs)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        #master.destroy()
    def record(self):
       
        while self.isrecording:
            data = self.stream.read(self.chunk)
            self.frames.append(data)


root = tk.Tk()
root.geometry("1366x768")
root.title("Summary Generator")
root['bg']='#272358'

buttonFont = font.Font(family='Times', size=16, weight='bold')

def Encryption():
    with open('filekey.key','rb') as Mykey:
        key = Mykey.read()
    
    f = Fernet(key)

    with open('summary.doc','rb') as org_file:
        original = org_file.read()

    encrypted = f.encrypt(original)
    with open('EncryptedFile.enc','wb') as enc_file:
        enc_file.write(encrypted)


def get_large_audio_transcription(path):
    sound = AudioSegment.from_wav(path)
    chunks = split_on_silence(sound,
        # experiment with this value for your target audio file
        min_silence_len = 500,
        # adjust this per requirement
        silence_thresh = sound.dBFS-14,
        # keep the silence for 1 second, adjustable as well
        keep_silence=500,
    )
    folder_name = "audio-chunks"
    if not os.path.isdir(folder_name):
        os.mkdir(folder_name)
    whole_text =""
    for i, audio_chunk in enumerate(chunks, start=1):
        chunk_filename = os.path.join(folder_name, f"chunk{i}.wav")
        audio_chunk.export(chunk_filename, format="wav")
        with sr.AudioFile(chunk_filename) as source:
            audio_listened = r.record(source)
            try:
                text = r.recognize_google(audio_listened)
            except sr.UnknownValueError as e:
                print("Error:", str(e))
            else:
                text = f"{text.capitalize()}. "
                print(chunk_filename, ":", text)
                whole_text += text
                with open('output.doc', 'w') as out:
                    out.writelines(whole_text)
    return whole_text

def BrowseFile():
    filename = filedialog.askopenfilename(initialdir = "/", title = "Select a File",
										filetypes = (("Audio file",
														"*.wav*"),
													("all files",

														"*.*")))
    get_large_audio_transcription(filename)
    Summary()
    sendMail()



def Summary():              # Summary Generate here
    import spacy
    from spacy.lang.en.stop_words import STOP_WORDS
    from string import punctuation
    from heapq import nlargest

    stopwords = list(STOP_WORDS)
    nlp = spacy.load("en_core_web_sm")
    with open('output.doc') as f:
        text = f.read()
    doc = nlp(text)
    print("\nOriginal Text: ", doc)
    tokens = [token.text for token in doc]
    word_frequencies = {}
    for word in doc:
        if word.text.lower() not in stopwords:
            if word.text.lower() not in punctuation:
                if word.text not in word_frequencies.keys():
                    word_frequencies[word.text] = 1
                else:
                    word_frequencies[word.text] += 1

    max_frequency = max(word_frequencies.values())
    for word in word_frequencies.keys():
        word_frequencies[word] = word_frequencies[word]/max_frequency
    sentence_tokens = [sent for sent in doc.sents]
    sentence_scores = {}
    for sent in sentence_tokens:
        for word in sent:
            if word.text.lower() in word_frequencies.keys():
                if sent not in sentence_scores.keys():
                    sentence_scores[sent] = word_frequencies[word.text.lower()]
                else:
                    sentence_scores[sent] += word_frequencies[word.text.lower()]

    
    select_length = int(len(sentence_tokens)*0.3)
    summary = nlargest(select_length, sentence_scores, key = sentence_scores.get)
    final_summary = [word.text for word in summary]
    summary = ' '.join(final_summary)

    with open('summary.doc', 'w') as out:
        out.writelines(summary)
    print("\nGenerated Summary: ",summary)
    print("Summary Generated")
    Encryption()




def clock():
    hour = time.strftime("%I")
    minute = time.strftime("%M")
    second = time.strftime("%S")
    day = time.strftime("%A")
    am_pm = time.strftime("%p")

    my_label.config(text=hour + ":" + minute + ":" + second + " " + am_pm)
    my_label.after(1000, clock)

    my_label2.config(text=day)





def sendMail():
    SenderAddress = "suyogmalkar18dhe@student.mes.ac.in"
    password = "2018HE0665"

    e = pd.read_excel("Email.xlsx")
    emails = e['Emails'].values

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(SenderAddress, password)

    msg = MIMEMultipart()

    msg['From'] = SenderAddress
    msg['Subject'] = "Meeting Summary"
    for email in emails:
        msg['To'] = email
    

    body = "From here you can decrypt the Encrypted Summary. Link --> https://drive.google.com/file/d/1sfF0D68JWZjBIUKRFkcan4T6FN2DjOao/view?usp=sharing "
    msg.attach(MIMEText(body, 'plain'))

    filename = "EncryptedFile.enc"
    attachment = open(filename, "rb")

    p = MIMEBase('application', 'octet-stream')

    p.set_payload((attachment).read())

    encoders.encode_base64(p)

    p.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    msg.attach(p)
    message = msg.as_string()
    for email in emails:
        server.sendmail(SenderAddress, email, message)
    
    server.quit()
    print("Mail has been sent ")
    messageWindow()

def messageWindow():
    global msgwindow
    msgwindow = tk.Tk()
    msgwindow.title("Message Box")
    msgwindow['bg']='#272358'
    w=250
    h=200
    scn_width = msgwindow.winfo_screenwidth()
    scn_height = msgwindow.winfo_screenheight()
    x = (scn_width / 2) - (w / 2)
    y = (scn_height / 2) - (h / 2)
    
    msgwindow.geometry(f'{w}x{h}+{int(x)}+{int(y)}')
    msgLabel = tk.Label(msgwindow, text="The summary has been sent! ",bg='#272358',fg='white',font=('Times',14,'bold')).place(x=2, y=70)
    msgButton = tk.Button(msgwindow, text="Ok", bd=8, bg='white',fg='#272358',font=('Times',14,'bold'), width=8, command=msgwindow.destroy).place(x=75, y=130)

    
    







my_label = tk.Label(text="", font=("Times",20,'bold'), fg="white", bg="#272358")
my_label.place(x=1140,y=600)

my_label2 = tk.Label(text="", font=("Times",17,'bold'), fg="white", bg="#272358")
my_label2.place(x=1170,y=650)
clock()



lbl = tk.Label(text="Summary Generation",bg='#272358',fg='white',font=('Times',40,'bold') ).place( x=425, y=50 )
btnRecord = tk.Button(text="Record", bd=10, bg='white', fg='#272358',font=buttonFont,height=1,width=20,command = Test).place( x=550, y=250 )  
btnBrowse = tk.Button(text="Browse", bd=10, bg='white', fg='#272358',font=buttonFont,width=20,command=BrowseFile).place( x=550, y=400 )




root.mainloop()

