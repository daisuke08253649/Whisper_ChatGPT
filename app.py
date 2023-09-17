import openai
import os
from flask import Flask, render_template, redirect, request, session, Response
from flask_dropzone import Dropzone
from datetime import datetime
from io import BytesIO
#from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
#from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph





pdfmetrics.registerFont(TTFont('ipag', './static/font/ipag.ttf'))

app = Flask(__name__)
dropzone = Dropzone(app)
app.secret_key = os.urandom(24)



#保存日時が最新のファイルを取得
def file(audio_f):
    #ファイルを保存するためのディレクトリを作成
    #user_name = os.environ['USERPROFILE'].split(os.sep)[-1]
    new_directory_path = f'/Users/daiya'
    save_directory_path = os.path.join(new_directory_path, 'OneDrive', 'デスクトップ', 'WHISCHAT')
    print(new_directory_path)
    print(save_directory_path)
    #ディレクトリが存在しない場合は作成する
    if not os.path.exists(save_directory_path):
        os.makedirs(save_directory_path)
        print('ディレクトリを作成しました')
    else:
        print('同じ名前のディレクトリが既に存在します')

    app.config['UPLOAD_FOLDER'] = save_directory_path
    FOLDER = app.config['UPLOAD_FOLDER']

    #ファイルを保存
    audio_path = os.path.join(FOLDER, audio_f.filename)
    audio_f.save(audio_path)
    print(os.path.isfile(audio_path))
    print('保存するファイルのパス:', audio_path)
    audio_files = os.listdir(FOLDER)
    file_datetimes = {}

    #最新のファイルを取得
    for a_file in audio_files:
        a_file_path = os.path.join(FOLDER, a_file)
        if os.path.isfile(a_file_path):
            file_time = os.path.getmtime(a_file_path)
            file_datetime = datetime.fromtimestamp(file_time)
            file_datetimes[a_file] = file_datetime
    new_file = max(file_datetimes, key=file_datetimes.get)
    print(new_file)
    print(file_datetime)
    return new_file, FOLDER



#whisperで文字起こし
def whisper(new_file, folder):
    audio_file_path = os.path.join(folder, new_file)
    file_path = open(audio_file_path, 'rb')
    print(audio_file_path)
    print(file_path)
    transcript = openai.Audio.transcribe("whisper-1", file_path)
    text = transcript.text
    return text



#chatgptで要約文作成
def chatgpt(whisper_text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {'role': 'system', 'content': '渡された文章を要約してください。また重要な点を箇条書きしてください'},
            {'role': 'user', 'content': whisper_text}
        ]
    )
    result = response.choices[0].message.content
    return result



#PDF化してダウンロード
def text_to_pdf(paragraphs):
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    style = styles['Normal']
    style.fontName = 'ipag'

    story = []
    for paragraph in paragraphs:
        p = Paragraph(paragraph, style)
        story.append(p)

    doc.build(story)

    response = Response(pdf_buffer.getvalue(), mimetype='application/pdf')
    response.headers['Content-Disposition'] = 'inline; filename=text_to_pdf.pdf'

    return response



#Flask
#ホーム画面
@app.route('/', methods=['GET', 'POST'])
def whisper_chatgpt():
    if request.method == 'POST':
        openai.api_key = request.form['api_key']
        audio_f = request.files['audio_file']
        a_file, folder = file(audio_f)
        whisper_text = whisper(a_file, folder)
        result = chatgpt(whisper_text)
        session['text_data'] = result
        return render_template('home.html', result=result)
    else:
        return render_template('home.html', text='※ここに議事録が表示されます')



#編集画面
@app.route('/edit', methods=['GET', 'POST'])
def edit():
    edit_text = session.get('text_data', '')
    return render_template('edit.html', edit_text=edit_text)



#PDFファイルのダウンロード
@app.route('/download_pdf')
def generate_text():
    text_data = session.get('text_data', '')
    text_paragraphs = text_data.split('\n')
    res = text_to_pdf(text_paragraphs)
    return res
    


#編集後、PDFファイルのダウンロード
@app.route('/edit_download_pdf', methods=['POST'])
def edit_generate_text():
    edited_data = request.form['edited_data']
    edited_paragraphs = edited_data.split('\n')
    res = text_to_pdf(edited_paragraphs)
    return res

    
    

    





if __name__ == '__main__':
    app.run(debug=True)
