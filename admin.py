from flask import Flask, request, render_template, redirect, url_for
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json
import os

app = Flask(__name__)
auth = HTTPBasicAuth()

# Задаем логин и пароль
users = {
    "admin": generate_password_hash("password")
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

# Путь для сохранения загруженных файлов
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Чтение данных кнопок из файла
def read_buttons():
    with open('buttons.json', 'r', encoding='utf-8') as file:
        return json.load(file)

# Чтение данных контента из файла
def read_content():
    with open('content.json', 'r', encoding='utf-8') as file:
        return json.load(file)

# Запись данных кнопок в файл
def write_buttons(buttons):
    with open('buttons.json', 'w', encoding='utf-8') as file:
        json.dump(buttons, file, ensure_ascii=False, indent=4)

# Запись данных контента в файл
def write_content(content):
    with open('content.json', 'w', encoding='utf-8') as file:
        json.dump(content, file, ensure_ascii=False, indent=4)

@app.route('/', methods=['GET', 'POST'])
@auth.login_required
def admin():
    if request.method == 'POST':
        button1_text = request.form.get('button1')
        button2_text = request.form.get('button2')
        button3_text = request.form.get('button3')
        buttons = read_buttons()
        buttons["button1"]["text"] = button1_text
        buttons["button2"]["text"] = button2_text
        buttons["button3"]["text"] = button3_text
        write_buttons(buttons)
        return redirect(url_for('admin'))
    
    buttons = read_buttons()
    return render_template('admin.html', buttons=buttons)

@app.route('/content', methods=['GET', 'POST'])
@auth.login_required
def content():
    if request.method == 'POST':
        content1 = request.form.get('content1')
        content2 = request.form.get('content2')
        content3 = request.form.get('content3')
        content = read_content()
        content["content1"] = content1
        content["content2"] = content2
        content["content3"] = content3
        write_content(content)
        return redirect(url_for('content'))

    buttons = read_buttons()
    content = read_content()
    return render_template('content.html', buttons=buttons, content=content)

@app.route('/subbuttons', methods=['GET', 'POST'])
@auth.login_required
def subbuttons():
    buttons = read_buttons()
    if request.method == 'POST':
        name = request.form.get('name')
        content = request.form.get('content')
        files = request.files.getlist('file')
        file_paths = []
        for file in files:
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                file_paths.append(file_path)
        if "button1_subbuttons" not in buttons:
            buttons["button1_subbuttons"] = []
        buttons["button1_subbuttons"].append({"name": name, "content": content, "files": file_paths, "buy_enabled": False})
        write_buttons(buttons)
        return redirect(url_for('subbuttons'))

    return render_template('subbuttons.html', buttons=buttons["button1_subbuttons"])

@app.route('/subbuttons/edit/<int:index>', methods=['GET', 'POST'])
@auth.login_required
def edit_subbutton(index):
    buttons = read_buttons()
    subbutton = buttons["button1_subbuttons"][index]
    if request.method == 'POST':
        name = request.form.get('name')
        content = request.form.get('content')
        files = request.files.getlist('file')
        file_paths = subbutton.get('files', [])
        
        # Сохранение загруженных файлов
        for file in files:
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                file_paths.append(file_path)
        
        # Добавление purchase_data
        purchase_text = request.form.get('purchase_text')
        purchase_files = request.files.getlist('purchase_files')
        purchase_file_paths = []
        
        for file in purchase_files:
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                purchase_file_paths.append(file_path)

        subbutton["purchase_data"] = {
            "text": purchase_text,
            "files": purchase_file_paths
        }
        
        buttons["button1_subbuttons"][index] = {
            "name": name,
            "content": content,
            "files": file_paths,
            "buy_enabled": subbutton["buy_enabled"],
            "purchase_data": subbutton["purchase_data"]
        }
        
        write_buttons(buttons)
        return redirect(url_for('subbuttons'))
    
    return render_template('edit_subbutton.html', index=index, subbutton=subbutton)

@app.route('/purchase_materials', methods=['GET', 'POST'])
@auth.login_required
def purchase_materials():
    buttons = read_buttons()
    if request.method == 'POST':
        subbutton_name = request.form.get('subbutton_name')
        purchase_text = request.form.get('purchase_text')
        purchase_files = request.files.getlist('purchase_files')
        file_paths = []
        for file in purchase_files:
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                file_paths.append(file_path)
        
        # Поиск нужной под-кнопки и сохранение данных
        for subbutton in buttons["button1_subbuttons"]:
            if subbutton["name"] == subbutton_name:
                subbutton["purchase_data"] = {"text": purchase_text, "files": file_paths}
                break
        
        write_buttons(buttons)

        # Отладка
        print(f"Сохранение данных purchase_data для под-кнопки '{subbutton_name}': {subbutton['purchase_data']}")
        
        return redirect(url_for('purchase_materials'))
    
    buttons = read_buttons()
    return render_template('purchase_materials.html', buttons=buttons["button1_subbuttons"])

@app.route('/subbuttons/delete/<int:index>', methods=['POST'])
@auth.login_required
def delete_subbutton(index):
    buttons = read_buttons()
    subbutton = buttons["button1_subbuttons"].pop(index)
    for file_path in subbutton.get('files', []):
        if os.path.exists(file_path):
            os.remove(file_path)
    write_buttons(buttons)
    return redirect(url_for('subbuttons'))

@app.route('/subbuttons/delete_file/<int:index>/<int:file_index>', methods=['POST'])
@auth.login_required
def delete_file(index, file_index):
    buttons = read_buttons()
    subbutton = buttons["button1_subbuttons"][index]
    file_path = subbutton["files"].pop(file_index)
    if os.path.exists(file_path):
        os.remove(file_path)
    write_buttons(buttons)
    return redirect(url_for('edit_subbutton', index=index))

@app.route('/subbuttons/enable_buy/<int:index>', methods=['POST'])
@auth.login_required
def enable_buy(index):
    buttons = read_buttons()
    buttons["button1_subbuttons"][index]["buy_enabled"] = True
    write_buttons(buttons)
    return redirect(url_for('subbuttons'))

@app.route('/purchase_materials/delete_file/<int:subbutton_index>/<int:file_index>', methods=['POST'])
@auth.login_required
def delete_purchase_file(subbutton_index, file_index):
    buttons = read_buttons()
    subbutton = buttons["button1_subbuttons"][subbutton_index]
    file_path = subbutton["purchase_data"]["files"].pop(file_index)
    if os.path.exists(file_path):
        os.remove(file_path)
    write_buttons(buttons)
    return redirect(url_for('purchase_materials'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
