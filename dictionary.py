import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk
from tkinter import *
from PIL import Image, ImageTk
import sqlite3
import os
from pathlib import Path
import time

directory = Path(__file__).parent 
recent_dbs_txt = os.path.join(directory, "recent_dbs.txt")
recent_db_path = {}
db_path = None
current_db_path = None
tooltip = None
tooltip_hide = None

#функции списка
def save_recent_dbs(db_path):
    '''сохраняет словари в файл'''
    if not db_path:
        return
    recent_dbs = load_recent_dbs()
    timestamp = str(int(time.time()))
    recent_dbs = [(path, ts) for path, ts in recent_dbs if path != db_path]
    recent_dbs.insert(0, (db_path, timestamp))
    recent_dbs = recent_dbs[:10]
    with open(recent_dbs_txt, "w") as file:
        for path, ts in recent_dbs:
            file.write(f"{path}|{ts}\n")
    refresh_listbox()
def load_recent_dbs():
    '''загружает словари в список'''
    valid_dbs = []
    if os.path.exists(recent_dbs_txt): #проверяется существует ли база
        with open(recent_dbs_txt, "r") as file:
            for line in file:
                parts = line.strip().split("|")
                if len(parts) == 2:
                    db_path, timestamp = parts
                    if os.path.exists(db_path):
                        valid_dbs.append((db_path, timestamp))
                else:
                    print(f"Пропуск: {line.strip()}")
    valid_dbs.sort(key=lambda x: int(x[1]), reverse=True) #сортировка списка по времени
    with open(recent_dbs_txt, "w") as file:
        for path, ts in valid_dbs:
            file.write(f"{path}|{ts}\n")
    return valid_dbs
def open_selected_db(event):
    '''открывает выбранный словарь в списке'''
    global db_path, current_db_path
    selected_db = listbox.curselection()
    if selected_db:
        selected_word = selected_db[0]
        selected_text = listbox.get(selected_word)
        full_path = recent_db_path.get(selected_text) #путь к словарю
        if full_path:
            current_db_path = full_path #запоминает открытую базу данных
            dictionary_window(full_path)
def refresh_listbox():
    '''перезагружает список'''
    listbox.delete(0, tk.END)
    recent_dbs = load_recent_dbs()
    recent_db_path.clear()
    for db_path, _ in recent_dbs:
        file_name = os.path.splitext(os.path.basename(db_path))[0]
        display_text = f"{file_name}"
        recent_db_path[display_text] = db_path
        listbox.insert(tk.END, display_text)

def main_menu_close():
    '''закрывает всю программу'''
    main_menu.quit()
    main_menu.destroy()

def button_create_database():
    '''кнопка создать словарь'''
    global current_db_path
    folder_path = filedialog.askdirectory(title="Выберите папку, в которой будет хранится ваш словарь")
    if not folder_path:
        return
    dictionary_name = simpledialog.askstring("Введите название словаря", "Введите название словаря:")
    if not dictionary_name:
        return
    file_path = os.path.join(folder_path, dictionary_name + ".db")
    try:
        conn = sqlite3.connect(file_path)
        conn.close()
        messagebox.showinfo("Успешно", f"Словарь создан в:\n{file_path}")
        save_recent_dbs(file_path)
        refresh_listbox()
        current_db_path = file_path
        dictionary_window(file_path)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось создать словарь:\n{e}")

def button_open_database():
    '''кнопка открыть словарь'''
    global current_db_path
    file_path = filedialog.askopenfilename(
        filetypes=[("SQLite Database", "*.db")],
        title="Выберите словарь"
    )
    if file_path:
        try:
            save_recent_dbs(file_path)
            current_db_path = file_path
            dictionary_window(file_path)
            refresh_listbox()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть словарь:\n{e}")

def show_warning(message):
    '''окно предупреждения'''
    warning_window = tk.Toplevel()
    warning_window.title("Внимание")
    warning_window.resizable(False, False)
    screen_width = warning_window.winfo_screenwidth()
    screen_height = warning_window.winfo_screenheight()
    x = (screen_width - 230) // 2
    y = (screen_height - 110) // 2
    warning_window.geometry(f"230x110+{x}+{y}")
    label_message = tk.Label(warning_window, text=message, font=("Arial", 12), pady=20)
    label_message.pack()
    button_close = ttk.Button(warning_window, text="Закрыть", command=warning_window.destroy)
    button_close.pack()
    warning_window.grab_set()
    warning_window.mainloop()

def refresh_words_list(db_path, listbox_words):
    '''обновляет список со словами'''
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT word, translation FROM words")
        words = cursor.fetchall()
        conn.close()
        listbox_words.delete(0, tk.END)
        for word, translation in words: 
            listbox_words.insert(tk.END, f"{word} - {translation}")
    except Exception as e:
        print(f"Ошибка при обновлении списка: {e}")

def dictionary_window(db_path):
    '''окно словаря'''
    global current_db_path, main_menu
    current_db_path = db_path #запоминает базу данных
    main_menu.withdraw()
    dictionary = tk.Toplevel()
    dictionary.title("Словарь")
    screen_width = dictionary.winfo_screenwidth()
    screen_height = dictionary.winfo_screenheight()
    x = (screen_width - 600) // 2
    y = (screen_height - 600) // 2
    dictionary.geometry(f"600x600+{x}+{y}") #размер окна
    dictionary.resizable(True, True)
    def return_to_main():
        '''вернуться в главное меню'''
        dictionary.destroy()
        main_menu.deiconify()
    dictionary.protocol("WM_DELETE_WINDOW", return_to_main)

    #ставит иконку
    icon = None
    icon_path = directory/"icon.ico"
    try:
        img = Image.open(icon_path)
        icon = ImageTk.PhotoImage(img)
        dictionary.iconphoto(False, icon)
    except Exception:
        print("Не удалось загрузить иконку")

    #текст
    dictionary_name = os.path.splitext(os.path.basename(db_path))[0]
    label_title = tk.Label(dictionary, text=f"{dictionary_name} словарь", font=("Arial", 12, "bold"))
    label_title.pack(pady=10)

    #кнопка добавить слово в словарь
    def add_word_window(db_path):
        '''окно добавления слова в словарь'''
        add_window = tk.Toplevel()
        add_window.title("Добавить слово")
        tk.Label(add_window, text="Введите слово:").pack()
        entry_word = tk.Entry(add_window)
        entry_word.pack()
        tk.Label(add_window, text="Введите перевод:").pack()
        entry_translation = tk.Entry(add_window)
        entry_translation.pack()
        def save():
            word = entry_word.get().strip()
            translation = entry_translation.get().strip()
            if not word or not translation:
                show_warning("Введите слово, и перевод")
                return
            save_word_to_db(db_path, word, translation)
            add_window.destroy()
        frame_buttons = tk.Frame(add_window)
        frame_buttons.pack(pady=10)
        button_save = ttk.Button(frame_buttons, text="Сохранить", command=save)
        button_save.pack(side=tk.LEFT, padx=5)
        button_cancel = ttk.Button(frame_buttons, text="Отмена", command=add_window.destroy)
        button_cancel.pack(side=tk.LEFT, padx=5)
        x = (screen_width - 200) // 2
        y = (screen_height - 130) // 2
        add_window.geometry(f"200x130+{x}+{y}")
        add_window.protocol("WM_ICONIFY", lambda *args: None) #нельзя свернуть окно
        add_window.resizable(False, False)
    button_add_word = ttk.Button(dictionary, text="Добавить слово", command=lambda: add_word_window(db_path))
    button_add_word.pack(pady=10, padx=20, anchor=W)
    
    def button_delete_selected_word():
        '''кнопка удаления слова'''
        selected_word = listbox_words.curselection()
        if not selected_word:
            messagebox.showwarning("Ошибка", "Выберите слово для удаления.")
            return
        selected_text = listbox_words.get(selected_word)
        word_to_delete = selected_text.split(" - ")[0]
        confirm = messagebox.askyesno("Удалить", f"Удалить слово '{word_to_delete}'?")
        if confirm:
            try:
                conn = sqlite3.connect(current_db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM words WHERE word = ?", (word_to_delete,))
                conn.commit()
                conn.close()
                refresh_words_list(current_db_path, listbox_words)
                messagebox.showinfo("Успешно", f"Слово '{word_to_delete}' удалено.")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить слово: {e}")
    button_delete_word = ttk.Button(dictionary, text="Удалить слово", command=button_delete_selected_word)
    button_delete_word.pack(pady=0, padx=20, anchor=W)
    
    #список со словами
    def refresh_local_word_list():
        '''обновляет список со словами'''
        listbox_words.delete(0, tk.END)
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT word, translation FROM words")
            words = cursor.fetchall()
            conn.close()
            for word, translation in words: 
                listbox_words.insert(tk.END, f"{word} - {translation}")
        except Exception as e:
            print(f"Ошибка при обновлении списка: {e}")
    def doubleclick_edit_word_window(db_path, listbox_words):
        '''редактировать слово по двойному нажатию на него'''
        selected_word = listbox_words.curselection()
        if not selected_word:
            messagebox.showwarning("Ошибка", "Выберите слово для редактирования.")
            return
        selected_text = listbox_words.get(selected_word)
        word, translation = selected_text.split(" - ", 1)
        edit_window = tk.Toplevel()
        edit_window.title("Редактировать слово")
        tk.Label(edit_window, text="Слово:").pack()
        entry_word = tk.Entry(edit_window)
        entry_word.pack()
        entry_word.insert(0, word)
        tk.Label(edit_window, text="Перевод:").pack()
        entry_translation = tk.Entry(edit_window)
        entry_translation.pack()
        entry_translation.insert(0, translation)
        def save_changes():
            '''сохранить изменения'''
            new_word = entry_word.get().strip()
            new_translation = entry_translation.get().strip()
            if not new_word or not new_translation:
                messagebox.showwarning("Ошибка", "Введите слово и перевод.")
                return
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("UPDATE words SET word = ?, translation = ? WHERE word = ?", 
                            (new_word, new_translation, word))
                conn.commit()
                conn.close()
                refresh_words_list(db_path, listbox_words)
                messagebox.showinfo("Успешно", "Слово обновлено")
                edit_window.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось обновить слово: {e}")
        frame_buttons = tk.Frame(edit_window)
        frame_buttons.pack(pady=10)
        button_save = ttk.Button(frame_buttons, text="Сохранить", command=save_changes)
        button_save.pack(side=tk.LEFT, padx=5)
        button_cancel = ttk.Button(frame_buttons, text="Отмена", command=edit_window.destroy)
        button_cancel.pack(side=tk.LEFT, padx=5)
        x = (screen_width - 200) // 2
        y = (screen_height - 130) // 2
        edit_window.geometry(f"200x130+{x}+{y}")
        edit_window.resizable(False, False)
    def save_word_to_db(db_path, word, translation):
        '''сохраняет слово в базу данных'''
        if not word or not translation:
            show_warning("Введите слово и перевод")
            return
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS words (id INTEGER PRIMARY KEY, word TEXT, translation TEXT)")
            cursor.execute("INSERT INTO words (word, translation) VALUES (?, ?)", (word, translation))
            conn.commit()
            conn.close()
            refresh_words_list(current_db_path, listbox_words)
            messagebox.showinfo("Успешно", "Слово добавлено в словарь")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить слово: {e}")
    listbox_words = tk.Listbox(dictionary, height=10, font=("Arial", 12))
    listbox_words.pack(fill=tk.BOTH, expand=True, padx=22, pady=14)
    listbox_words.bind("<Double-Button-1>", lambda event: doubleclick_edit_word_window(current_db_path, listbox_words))

    #кнопка назад в меню
    button_back = ttk.Button(dictionary, text="Назад в меню", command=return_to_main)
    button_back.pack(pady=10)

    refresh_local_word_list()
    dictionary.mainloop()

def show_tooltip(event):
    '''показывает подсказку'''
    global tooltip, tooltip_hide
    hide_tooltip()
    selected = listbox.nearest(event.y)
    if selected >= 0:
        selected_name = listbox.get(selected)
        full_path = recent_db_path.get(selected_name)
        if full_path:
            tooltip = tk.Toplevel(main_menu)
            tooltip.wm_overrideredirect(True)
            tooltip.geometry(f"+{main_menu.winfo_pointerx() + 10}+{main_menu.winfo_pointery() + 10}")
            label = tk.Label(tooltip, text=full_path, background="lightyellow", relief="solid", borderwidth=1)
            label.pack()
            if tooltip_hide is not None:
                main_menu.after_cancel(tooltip_hide)
            tooltip_hide = main_menu.after(1500, hide_tooltip)
def hide_tooltip(event=None):
    '''убирает подсказку'''
    global tooltip, tooltip_hide
    if tooltip and tooltip.winfo_exists():
        tooltip.destroy()
        tooltip = None
    tooltip_hide = None

def button_delete_database():
    '''кнопка удаления словаря'''
    selected = listbox.curselection()
    if not selected:
        messagebox.showwarning("Ошибка", "Выберите словарь для удаления.")
        return
    selected_text = listbox.get(selected)
    db_path = recent_db_path.get(selected_text)
    if not db_path:
        messagebox.showerror("Ошибка", "Не удалось найти путь к выбранному словарю.")
        return
    confirm = messagebox.askyesno("Подтвердить", f"Вы уверены, что хотите удалить словарь {selected_text}?")
    if confirm:
        try:
            os.remove(db_path)
            messagebox.showinfo("Успешно", f"Словарь {selected_text} удален.")
            recent_dbs = load_recent_dbs()
            recent_dbs = [db for db in recent_dbs if db[0] != db_path]
            with open(recent_dbs_txt, "w") as file:
                for path, ts in recent_dbs:
                    file.write(f"{path}|{ts}\n")
            refresh_listbox()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить словарь: {e}")

#главное меню
main_menu = tk.Tk()
main_menu.title("Словари")
main_menu.protocol("WM_DELETE_WINDOW", main_menu_close)
#определяется размер монитора, для появления окна в центре экрана
screen_width = main_menu.winfo_screenwidth()
screen_height = main_menu.winfo_screenheight()
x = (screen_width - 385) // 2
y = (screen_height - 465) // 2
main_menu.geometry(f"385x465+{x}+{y}") #размер окна
main_menu.resizable(False, False)

#иконка окна
icon = None
icon_path = directory/"icon.ico"
try:
    img = Image.open(icon_path)
    icon = ImageTk.PhotoImage(img)
    main_menu.iconphoto(False, icon)
except Exception:
    print("Не удалось загрузить иконку")

#текст
label = ttk.Label(text="Словарь иностранных слов", font=("Arial", 17))
label.pack()

#кнопка открыть словарь
button_open = ttk.Button(main_menu, text="Открыть существующий словарь", command=button_open_database)
button_open.pack(pady=5, anchor=N)

#кнопка создать словарь
button_create = ttk.Button(main_menu, text="Создать словарь", command=button_create_database)
button_create.pack(pady=2)

#список с недавно открытыми или созданными словарями
tooltip = None
listbox = tk.Listbox(main_menu, font=("Arial", 13))
listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
listbox.bind("<Double-Button-1>", open_selected_db)
listbox.bind("<Motion>", show_tooltip)
listbox.bind("<Leave>", hide_tooltip)
#загружает словари в список
recent_dbs = load_recent_dbs()
for db_path, _ in recent_dbs:
        file_name = os.path.splitext(os.path.basename(db_path))[0]
        recent_db_path[file_name] = db_path
        listbox.insert(tk.END, file_name)

#кнопка удаления
button_delete = ttk.Button(main_menu, text="Удалить словарь", command=button_delete_database)
button_delete.pack(pady=5)

#кнопка закрыть программу
button_programmclose = ttk.Button(main_menu, text="Выйти из программы", command=main_menu_close)
button_programmclose.pack(anchor=S, expand=True, pady=10)

main_menu.update_idletasks()
main_menu.mainloop()