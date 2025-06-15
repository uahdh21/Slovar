import os
import sqlite3
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk
from tkinter import *
from pathlib import Path
import time
from datetime import datetime
import random

py_path = Path(__file__).parent

recent_dbs_sqlite = os.path.join(py_path, "recent_dbs.sqlite")
recent_db_path = {}

def button_create_db():
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
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS database_metadata (
                        id INTEGER PRIMARY KEY,
                        created_at TEXT,
                        last_opened_at TEXT
                      )''')
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO database_metadata (created_at, last_opened_at) VALUES (?, ?)", 
                   (created_at, created_at))
        conn.commit()
        messagebox.showinfo("Успешно", f"Словарь создан в:\n{file_path}")
        set_creation_time(file_path)
        save_recent_db(file_path)
        refresh_listbox()
        current_db_path = file_path
        dictionary_window(file_path)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось создать словарь:\n{e}")

def button_open_db():
    global current_db_path
    file_path = filedialog.askopenfilename(
        filetypes=[("SQLite Database", "*.db")],
        title="Выберите словарь"
    )
    if file_path:
        try:
            update_last_opened_time(file_path)
            save_recent_db(file_path)
            current_db_path = file_path
            refresh_listbox()
            dictionary_window(file_path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть словарь:\n{e}")

def save_recent_db(db_path):
    '''сохраняет список словарей'''
    if not db_path:
        return
    conn = sqlite3.connect(recent_dbs_sqlite)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recent_dbs (
            path TEXT PRIMARY KEY,
            timestamp INTEGER
        )
    """)
    timestamp = int(time.time())
    cursor.execute("INSERT OR REPLACE INTO recent_dbs (path, timestamp) VALUES (?, ?)", (db_path, timestamp))
    conn.commit()
    conn.close()
    refresh_listbox()

def create_metadata_table(db_path):
    '''создаёт информацию о создании и открытия словаря'''
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS database_metadata (
                id INTEGER PRIMARY KEY,
                created_at TEXT,
                last_opened_at TEXT
            )
        ''')
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка: {e}")

def set_creation_time(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO database_metadata (created_at, last_opened_at)
            VALUES (?, ?)
        ''', (created_at, created_at))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка: {e}")

def update_last_opened_time(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        last_opened_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("UPDATE database_metadata SET last_opened_at = ? WHERE id = 1", 
                   (last_opened_at,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка: {e}")

def get_metadata(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='database_metadata';")
        if not cursor.fetchone():
            raise ValueError("Table 'database_metadata' does not exist in the database.")
        cursor.execute('SELECT created_at, last_opened_at FROM database_metadata WHERE id = 1')
        metadata = cursor.fetchone()
        if metadata is None:
            raise ValueError("Metadata not found for id = 1.")
        conn.close()
        return metadata
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

def load_recent_db():
    '''загружает словари в список'''
    valid_dbs = []
    if os.path.exists(recent_dbs_sqlite):
        conn = sqlite3.connect(recent_dbs_sqlite)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recent_dbs (
                path TEXT PRIMARY KEY,
                timestamp INTEGER
            )
        """)
        cursor.execute("SELECT path, timestamp FROM recent_dbs ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()
        for path, timestamp in rows:
            if os.path.exists(path):
                valid_dbs.append((path, str(timestamp)))
        conn = sqlite3.connect(recent_dbs_sqlite)
        cursor = conn.cursor()
        for path, timestamp in rows:
            if not os.path.exists(path):
                cursor.execute("DELETE FROM recent_dbs WHERE path = ?", (path,)) #удаляет словари если их нет
        conn.commit()
        conn.close()
    return valid_dbs

def open_selected_db(event):
    '''открывает выбранный словарь в списке'''
    global current_db_path
    selected_db = listbox.curselection()
    if selected_db:
        selected_word = selected_db[0]
        selected_text = listbox.get(selected_word)
        full_path = recent_db_path.get(selected_text) #путь к словарю
        if full_path:
            current_db_path = full_path #запоминает открытый в данный момент словарь
            update_last_opened_time(full_path)
            dictionary_window(full_path)

def refresh_listbox():
    '''обновляет список'''
    listbox.delete(0, tk.END)
    recent_dbs = load_recent_db()
    recent_db_path.clear()
    for db_path, _ in recent_dbs:
        file_name = os.path.splitext(os.path.basename(db_path))[0]
        display_text = f"{file_name}"
        recent_db_path[display_text] = db_path
        listbox.insert(tk.END, display_text)

def show_database_info():
    selected = listbox.curselection()
    if not selected:
        messagebox.showerror("Ошибка", "Сначала выберите базу данных!")
        return
    selected_index = selected[0]
    selected_db = listbox.get(selected_index)
    db_path = recent_db_path.get(selected_db)
    metadata = get_metadata(db_path)
    if metadata:
        created_at, last_opened_at = metadata
        db_name = os.path.splitext(os.path.basename(selected_db))[0]
        display_info(db_name, db_path, created_at, last_opened_at)
    else:
        messagebox.showerror("Ошибка", "Не удалось получить информацию о базе данных.")

def button_delete_db():
    selected = listbox.curselection()
    if not selected:
        messagebox.showwarning("Ошибка", "Выберите словарь для удаления.")
        return
    selected_index = selected[0]
    selected_db = listbox.get(selected_index)
    db_path = recent_db_path.get(selected_db)
    if not db_path:
        messagebox.showerror("Ошибка", "Не удалось найти путь к выбранному словарю.")
        return
    confirm = messagebox.askyesno("Подтвердить", f"Вы уверены, что хотите удалить словарь {selected_db}?")
    if confirm:
        try:
            os.remove(db_path)
            messagebox.showinfo("Успешно", f"Словарь {selected_db} удален.")
            recent_dbs = load_recent_db()
            conn = sqlite3.connect(recent_dbs_sqlite)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recent_dbs WHERE path = ?", (db_path,))
            conn.commit()
            conn.close()
            refresh_listbox()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить словарь: {e}")

def warning_window(message):
    warning_window = tk.Toplevel()
    warning_window.title("Внимание")
    warning_window.resizable(False, False)
    screen_width = warning_window.winfo_screenwidth()
    screen_height = warning_window.winfo_screenheight()
    x = (screen_width - 230) // 2
    y = (screen_height - 110) // 2
    warning_window.geometry(f"230x110+{x}+{y}")
    label_message = ttk.Label(warning_window, text=message, font=("Arial", 12), pady=20)
    label_message.pack()
    button_close = ttk.Button(warning_window, text="ОК", command=warning_window.destroy)
    button_close.pack()
    warning_window.grab_set()
    warning_window.mainloop()

def display_info(db_name, db_path, created_at, last_opened_at):
    info_text = (
        f"Имя базы данных: {db_name}\n"
        f"Путь: {db_path}\n"
        f"Дата создания: {created_at}\n"
        f"Последнее открытие: {last_opened_at}"
    )
    info_window = tk.Toplevel()
    info_window.title("Информация о словаре")
    info_window.resizable(True, True)
    screen_width = info_window.winfo_screenwidth()
    screen_height = info_window.winfo_screenheight()
    x = (screen_width - 350) // 2
    y = (screen_height - 135) // 2
    info_window.geometry(f"350x135+{x}+{y}")
    label = tk.Label(info_window, text=info_text, justify="left", anchor="center", padx=10, pady=10, font=("Arial", 12))
    label.pack(fill="both", expand=True)
    close_button = tk.Button(info_window, text="ОК", command=info_window.destroy)
    close_button.pack()

def refresh_listbox_words(db_path, listbox_words):
    '''обновляет список со словами'''
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT word FROM words")
        words = cursor.fetchall()
        conn.close()
        listbox_words.delete(0, tk.END)
        for (word,) in words:
            listbox_words.insert(tk.END, word)
    except Exception as e:
        print(f"Ошибка при обновлении списка: {e}")

def refresh_listbox_translations(db_path, listbox_translations):
    '''обновляет список с переводом'''
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT translation FROM words")
        translations = cursor.fetchall()
        conn.close()
        listbox_translations.delete(0, tk.END)
        for (translation,) in translations:
            listbox_translations.insert(tk.END, translation)
    except Exception as e:
        print(f"Ошибка при обновлении списка: {e}")

def dictionary_window(db_path):
    correct_translations = []
    user_answers = []
    option_menus = []
    seconds_elapsed = 0
    quiz_active = False
    timer_id = None
    select_window = None
    scale = None
    global current_db_path, listbox_words, listbox_translations, search_var_words, search_var_translations
    current_db_path = db_path #запоминает базу данных
    start_window.withdraw()
    dictionary = tk.Toplevel()
    dictionary.title("Словарь")
    screen_width = dictionary.winfo_screenwidth()
    screen_height = dictionary.winfo_screenheight()
    x = (screen_width - 533) // 2
    y = (screen_height - 680) // 2
    dictionary.geometry(f"533x680+{x}+{y}") #размер окна
    dictionary.resizable(False, False)
    def return_to_start_window():
        dictionary.destroy()
        start_window.deiconify()
    dictionary.protocol("WM_DELETE_WINDOW", return_to_start_window)

    dictionary.grid_rowconfigure(4, weight=1)

    def save_word_to_db(db_path, word, translation, part_of_speech):
        if not word or not translation:
            warning_window("Введите слово и перевод")
            return
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS words (id INTEGER PRIMARY KEY, word TEXT, translation TEXT, part_of_speech TEXT)")
            cursor.execute("INSERT INTO words (word, translation, part_of_speech) VALUES (?, ?, ?)", (word, translation, part_of_speech))
            conn.commit()
            conn.close()
            refresh_words_list()
            messagebox.showinfo("Успешно", "Слово добавлено в словарь")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить слово: {e}")

    #текст
    dictionary_name = os.path.splitext(os.path.basename(db_path))[0]
    dictionary_title = tk.Label(dictionary, text=f"{dictionary_name} словарь", font=("Arial", 14, "bold"))
    dictionary_title.grid(row=0, column=0, columnspan=6, pady=10)

    #кнопка добавить слово
    def add_word(db_path):
        add_window = tk.Toplevel()
        add_window.title("Добавить слово")
        ttk.Label(add_window, text="Введите слово:").pack()
        entry_word = ttk.Entry(add_window)
        entry_word.pack()
        ttk.Label(add_window, text="Введите перевод:").pack()
        entry_translation = ttk.Entry(add_window)
        entry_translation.pack()
        ttk.Label(add_window, text="Выберите часть речи:").pack()
        #список с частью речи
        part_of_speech_var = tk.StringVar()
        combo_part_of_speech = ttk.Combobox(add_window, textvariable=part_of_speech_var, state="readonly")
        combo_part_of_speech['values'] = ("Существительное", "Глагол", "Прилагательное", "Наречие", "Местоимение", "Предлог", "Союз", "Междометие", "Числительное", "Другое")
        combo_part_of_speech.pack()
        combo_part_of_speech.current(0)
        def save():
            word = entry_word.get().strip()
            translation = entry_translation.get().strip()
            part_of_speech = part_of_speech_var.get().strip()
            if not word or not translation or not part_of_speech:
                warning_window("Введите слово, перевод или выберите часть речи")
                return
            save_word_to_db(db_path, word, translation, part_of_speech)
            add_window.destroy()
        frame_buttons = ttk.Frame(add_window)
        frame_buttons.pack(pady=10)
        button_save = ttk.Button(frame_buttons, text="Сохранить", command=save)
        button_save.pack(side=tk.LEFT, padx=5)
        button_cancel = ttk.Button(frame_buttons, text="Отмена", command=add_window.destroy)
        button_cancel.pack(side=tk.LEFT, padx=5)
        x = (screen_width - 217) // 2
        y = (screen_height - 187) // 2
        add_window.geometry(f"217x187+{x}+{y}")
        add_window.protocol("WM_ICONIFY", lambda *args: None)
        add_window.resizable(True, True)
    button_add_word = ttk.Button(dictionary, text="Добавить слово", command=lambda: add_word(db_path))
    button_add_word.grid(row=1, column=0, pady=5, padx=13, ipadx=7, ipady=2, sticky=W)

    def button_delete_selected_word():
        selected_word = listbox_words.curselection()
        selected_translation = listbox_translations.curselection()
        if selected_word:
            index = selected_word[0]
            displayed_word = listbox_words.get(index)
            translation_to_delete = listbox_translations.get(index)
        elif selected_translation:
            index = selected_translation[0]
            displayed_word = listbox_words.get(index)
            translation_to_delete = listbox_translations.get(index)
        else:
            messagebox.showwarning("Ошибка", "Выберите слово или перевод для удаления.")
            return
        displayed_word = listbox_words.get(index)
        word_to_delete = displayed_word.split(". ", 1)[1].rsplit(" (", 1)[0]
        confirm = messagebox.askyesno("Удалить", f"Удалить слово '{word_to_delete}'?")
        if confirm:
            try:
                conn = sqlite3.connect(current_db_path)
                cursor = conn.cursor()
                cursor.execute("DELETE FROM words WHERE word = ? AND translation = ?", (word_to_delete, translation_to_delete))
                conn.commit()
                conn.close()
                refresh_words_list()
                messagebox.showinfo("Успешно", f"Слово '{word_to_delete}' удалено.")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить слово: {e}")
    button_delete_word = ttk.Button(dictionary, text="Удалить слово", command=button_delete_selected_word)
    button_delete_word.grid(row=1, column=5, pady=5, padx=13, ipadx=7, ipady=2, sticky=E)

    def filter_words(event=None):
        '''фильтрует список слов по введенному запросу'''
        query = search_var_words.get().strip().lower()
        pos_filter = part_of_speech_var.get().strip().lower()
        listbox_words.delete(0, tk.END)
        listbox_translations.delete(0, tk.END)
        search_var_translations.set("")
        try:
            conn = sqlite3.connect(current_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT word, translation, part_of_speech FROM words")
            words = cursor.fetchall()
            conn.close()
            filtered = [(word, translation, pos) for word, translation, pos in words
            if (query in word.lower()) and (pos_filter == "" or pos.lower() == pos_filter)]
            for i, (word, translation, pos) in enumerate(filtered, start=1):
                if (query in word.lower()) and (pos_filter == "" or pos.lower() == pos_filter):
                    listbox_words.insert(tk.END, f"{i}. {word} ({pos})")
                    listbox_translations.insert(tk.END, translation)
        except Exception as e:
            print(f"Ошибка при фильтрации списка: {e}")

    def filter_translations(event=None):
        query = search_var_translations.get().strip().lower()
        pos_filter = part_of_speech_var.get().strip().lower()
        listbox_words.delete(0, tk.END)
        listbox_translations.delete(0, tk.END)
        search_var_words.set("")
        try:
            conn = sqlite3.connect(current_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT word, translation, part_of_speech FROM words")
            words = cursor.fetchall()
            conn.close()
            filtered = [(word, translation, pos) for word, translation, pos in words
            if (query in translation.lower()) and (pos_filter == "" or pos.lower() == pos_filter)]
            for i, (word, translation, pos) in enumerate(filtered, start=1):
                if (query in translation.lower()) and (pos_filter == "" or pos.lower() == pos_filter):
                    listbox_words.insert(tk.END, f"{i}. {word} ({pos})")
                    listbox_translations.insert(tk.END, translation)
        except Exception as e:
            print(f"Ошибка при фильтрации списка: {e}")

    #поле для ввода слова
    search_var_words = tk.StringVar()
    search_entry_words = ttk.Entry(dictionary, textvariable=search_var_words, width=30)
    search_entry_words.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
    search_entry_words.bind("<KeyRelease>", filter_words)

    search_var_translations = tk.StringVar()
    search_entry_translations = ttk.Entry(dictionary, textvariable=search_var_translations, width=30)
    search_entry_translations.grid(row=2, column=2, columnspan=4, padx=10, pady=5, sticky="ew")
    search_entry_translations.bind("<KeyRelease>", filter_translations)

    part_of_speech_var = tk.StringVar()
    part_of_speech_combobox = ttk.Combobox(dictionary, textvariable=part_of_speech_var, state="readonly")
    part_of_speech_combobox['values'] = ["", "Существительное", "Глагол", "Прилагательное", "Наречие", "Местоимение", "Предлог", "Союз", "Междометие", "Числительное", "Другое"]
    part_of_speech_combobox.set("")
    part_of_speech_combobox.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
    part_of_speech_combobox.bind("<<ComboboxSelected>>", filter_words)

    #список со словами
    def refresh_words_list():
        '''обновляет список'''
        listbox_words.delete(0, tk.END)
        listbox_translations.delete(0, tk.END)
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT word, translation, part_of_speech FROM words")
            words = cursor.fetchall()
            conn.close()
            for i, (word, translation, part_of_speech) in enumerate(words, start=1):
                display_word = f"{word} ({part_of_speech})" if part_of_speech else word
                listbox_words.insert(tk.END, f"{i}. {word} ({part_of_speech})")
                listbox_translations.insert(tk.END, translation)
        except Exception as e:
            print(f"Ошибка при обновлении списка: {e}")
    def edit_word(db_path, listbox_words, listbox_translations):
        '''редактировать слово по двойному нажатию на него'''
        selected_word = listbox_words.curselection()
        selected_translation = listbox_translations.curselection()
        if selected_word:
            index = selected_word[0]
            displayed_word = listbox_words.get(index)
            translation = listbox_translations.get(index)
        elif selected_translation:
            index = selected_translation[0]
            translation = listbox_translations.get(index)
            displayed_word = listbox_words.get(index)
        else:
            messagebox.showwarning("Ошибка", "Выберите слово или перевод для редактирования.")
            return
        displayed_word = listbox_words.get(index)
        word = displayed_word.split(". ", 1)[1].rsplit(" (", 1)[0]
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT part_of_speech FROM words WHERE word = ? AND translation = ?", (word, translation))
        result = cursor.fetchone()
        conn.close()
        part_of_speech = result[0] if result else ""
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
        tk.Label(edit_window, text="Часть речи:").pack()
        part_of_speech_var = tk.StringVar()
        combo_part_of_speech = ttk.Combobox(edit_window, textvariable=part_of_speech_var, state="readonly")
        combo_part_of_speech['values'] = ("Существительное", "Глагол", "Прилагательное", "Наречие", "Местоимение", "Предлог", "Союз", "Междометие", "Числительное", "Другое")
        combo_part_of_speech.pack()
        if part_of_speech in combo_part_of_speech['values']:
            combo_part_of_speech.set(part_of_speech)
        else:
            combo_part_of_speech.current(0)
        def save_changes():
            '''сохранить изменения'''
            new_word = entry_word.get().strip()
            new_translation = entry_translation.get().strip()
            new_part_of_speech = part_of_speech_var.get().strip()
            if not new_word or not new_translation:
                messagebox.showwarning("Ошибка", "Введите слово и перевод.")
                return
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("UPDATE words SET word = ?, translation = ?, part_of_speech = ? WHERE word = ? AND translation = ?",
                            (new_word, new_translation, new_part_of_speech, word, translation))
                conn.commit()
                conn.close()
                refresh_words_list()
                messagebox.showinfo("Успешно", "Слово обновлено")
                edit_window.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось обновить слово: {e}")
        frame_buttons = tk.Frame(edit_window)
        frame_buttons.pack(pady=10)
        button_save = tk.Button(frame_buttons, text="Сохранить", command=save_changes)
        button_save.pack(side=tk.LEFT, padx=5)
        button_cancel = tk.Button(frame_buttons, text="Отмена", command=edit_window.destroy)
        button_cancel.pack(side=tk.LEFT, padx=5)
        x = (screen_width - 217) // 2
        y = (screen_height - 187) // 2
        edit_window.geometry(f"217x187+{x}+{y}")
        edit_window.resizable(False, False)
    listbox_words = tk.Listbox(dictionary, height=10, font=("Arial", 12))
    listbox_words.grid(row=4, column=0, columnspan=2, padx=8, pady=0, sticky=NSEW)
    listbox_words.bind("<Double-Button-1>", lambda event: edit_word(db_path, listbox_words, listbox_translations))

    listbox_translations = tk.Listbox(dictionary, height=10, font=("Arial", 12))
    listbox_translations.grid(row=4, column=2, columnspan=4, padx=8, pady=0, sticky=NSEW)
    listbox_translations.bind("<Double-Button-1>", lambda event: edit_word(db_path, listbox_words, listbox_translations))
    
    def quiz(current_db_path):

        def get_total_words():
            conn = sqlite3.connect(current_db_path)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='words'")
                if cursor.fetchone() is None:
                    return 0
                cursor.execute("SELECT COUNT(*) FROM words")
                count = cursor.fetchone()[0]
                return count
            except sqlite3.Error as e:
                print(f"Ошибка базы данных: {e}")
                return 0
            finally:
                conn.close()

        def load_words(n):
            conn = sqlite3.connect(current_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT word, translation FROM words")
            data = cursor.fetchall()
            conn.close()
            random.shuffle(data)
            return data[:n]

        def restart_quiz(quiz_window):
            quiz_window.destroy()
            quiz_choose_window.deiconify()

        def update_timer(label, quiz_window):
            nonlocal seconds_elapsed, timer_id, quiz_active
            if quiz_active:
                seconds_elapsed += 1
                label.config(text=f"Время: {seconds_elapsed} сек")
                timer_id = quiz_window.after(1000, update_timer, label, quiz_window)

        def open_quiz_window(selected_words):
            nonlocal correct_translations, user_answers, option_menus
            nonlocal seconds_elapsed, quiz_active, timer_id

            quiz_window = tk.Toplevel(quiz_choose_window)
            quiz_window.title("Викторина")
            frame = tk.Frame(quiz_window)
            frame.pack(padx=20, pady=20)

            correct_translations = []
            user_answers = []
            option_menus = []

            all_translations = [t for _, t in load_words(100)]
            seconds_elapsed = 0
            quiz_active = True
            button_refs = {}

            for i, (word, correct_translation) in enumerate(selected_words):
                tk.Label(frame, text=f"{i+1}. {word}").grid(row=i, column=0, sticky="w")
                all_other_translations = [t for t in all_translations if t != correct_translation]
                options = random.sample(all_other_translations, k=min(2, len(all_other_translations)))
                options.append(correct_translation)
                random.shuffle(options)
                var = tk.StringVar(value="")
                option_menu = tk.OptionMenu(frame, var, *options)
                option_menu.grid(row=i, column=1, sticky="ew")
                correct_translations.append(correct_translation)
                user_answers.append(var)
                option_menus.append(option_menu)

            timer_label = tk.Label(frame, text="Время: 0 сек", fg="blue")
            timer_label.grid(row=len(selected_words), column=0, columnspan=2, pady=(10, 0))
            timer_id = quiz_window.after(1000, update_timer, timer_label, quiz_window)

            check_button = tk.Button(frame, text="Проверить")
            check_button.config(command=lambda: check_results(check_button, quiz_window, timer_id, button_refs))
            check_button.grid(row=len(selected_words)+1, column=0, columnspan=2, pady=10)

            show_answers_button = tk.Button(frame, text="Показать правильные ответы", command=lambda: show_correct_answers(selected_words, user_answers, check_button))
            show_answers_button.grid(row=len(selected_words)+2, column=0, columnspan=2, pady=(0, 10))
            show_answers_button.grid_remove() #скрывает до проверки
            button_refs["show_answers_button"] = show_answers_button

        def check_results(check_button, quiz_window, timer_id, button_refs):
            nonlocal quiz_active
            quiz_window.after_cancel(timer_id)
            quiz_active = False
            score = 0
            for correct, var, menu in zip(correct_translations, user_answers, option_menus):
                chosen = var.get()
                if chosen == correct:
                    menu.config(bg='lightgreen')
                    score += 1
                else:
                    menu.config(bg='lightcoral')
            messagebox.showinfo("Результат", f"Правильных ответов: {score} из {len(correct_translations)}")
            check_button.config(text="Заново", command=lambda: restart_quiz(quiz_window))
            button_refs["show_answers_button"].grid()

        def show_correct_answers(selected_words, user_answers, check_button):
            answers_window = tk.Toplevel()
            answers_window.title("Правильные ответы")
            tk.Label(answers_window, text="Слово", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=10, pady=5)
            tk.Label(answers_window, text="Правильный перевод", font=("Arial", 10, "bold")).grid(row=0, column=1, padx=10)
            tk.Label(answers_window, text="Ваш ответ", font=("Arial", 10, "bold")).grid(row=0, column=2, padx=10)

            for i, ((word, correct), var) in enumerate(zip(selected_words, user_answers)):
                chosen = var.get()
                result = "✅" if chosen == correct else "❌"
                tk.Label(answers_window, text=word).grid(row=i+1, column=0, padx=10, sticky="w")
                tk.Label(answers_window, text=correct).grid(row=i+1, column=1, padx=10, sticky="w")
                tk.Label(answers_window, text=f"{chosen} {result}").grid(row=i+1, column=2, padx=10, sticky="w")

        def on_start():
            n = scale.get()
            selected = load_words(n)
            if len(selected) < 1:
                messagebox.showerror("Ошибка", "Недостаточно слов в словаре.")
                return
            if len(selected) < 3:
                messagebox.showwarning("Внимание", f"В словаре всего {len(selected)} слов. Варианты ответов будут ограничены.")
            quiz_choose_window.withdraw()
            open_quiz_window(selected)
        quiz_choose_window = tk.Toplevel()
        quiz_choose_window.title("Выбор количества слов")
        total_words = get_total_words()
        if total_words == 0:
            messagebox.showerror("Ошибка", "В словаре нет слов.")
            quiz_choose_window.destroy()
            return
        frame = tk.Frame(quiz_choose_window)
        frame.pack(pady=20, padx=20)
        tk.Label(frame, text="Выберите количество слов:").pack()
        scale = tk.Scale(frame, from_=1, to=total_words, orient=tk.HORIZONTAL, length=300)
        scale.set(min(10, total_words))
        scale.pack()
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Начать", command=on_start).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Выйти", command=quiz_choose_window.destroy).pack(side=tk.LEFT, padx=5)

        correct_translations = []
        user_answers = []
        option_menus = []
        seconds_elapsed = 0
        quiz_active = False
        timer_id = None

    button_start_exercise = ttk.Button(dictionary, text="Запоминать слова", command=lambda: quiz(current_db_path))
    button_start_exercise.grid(row=5, column=0, pady=10, ipadx=30, ipady=2, columnspan=6)

    #кнопка назад в меню
    button_back = ttk.Button(dictionary, text="Назад в меню", command=return_to_start_window)
    button_back.grid(row=6, column=0, pady=10, ipadx=30, ipady=2, columnspan=6)

    refresh_words_list()
    dictionary.mainloop()

start_window = tk.Tk()
start_window.title("Словари")
start_window.protocol("WM_DELETE_WINDOW", start_window.destroy)
screen_width = start_window.winfo_screenwidth()
screen_height = start_window.winfo_screenheight()
x = (screen_width - 385) // 2
y = (screen_height - 465) // 2
start_window.geometry(f"385x465+{x}+{y}") #размер окна
start_window.resizable(False, False)

label = ttk.Label(text="Словарь иностранных слов", font=("Arial", 17))
label.pack()

button_open = ttk.Button(start_window, text="Открыть существующий словарь", command=button_open_db)
button_open.pack(pady=5, anchor=N)

button_create = ttk.Button(start_window, text="Создать словарь", command=button_create_db)
button_create.pack(pady=2)

#список с недавно открытыми или созданными словарями
listbox = tk.Listbox(start_window, font=("Arial", 13))
listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
listbox.bind("<Double-Button-1>", open_selected_db)
#загружает словари в список
recent_dbs = load_recent_db()
for db_path, _ in recent_dbs:
        file_name = os.path.splitext(os.path.basename(db_path))[0]
        recent_db_path[file_name] = db_path
        listbox.insert(tk.END, file_name)

button_show_info = ttk.Button(start_window, text="Показать информацию о словаре", command=show_database_info)
button_show_info.pack(pady=5)

button_delete = ttk.Button(start_window, text="Удалить словарь", command=button_delete_db)
button_delete.pack(pady=5)

button_programmclose = ttk.Button(start_window, text="Выйти из программы", command=start_window.destroy)
button_programmclose.pack(anchor=S, expand=True, pady=10)

start_window.update_idletasks()
start_window.mainloop()
