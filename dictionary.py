#импорт библиотек
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, ttk
from tkinter import *
import sqlite3
import os
from pathlib import Path
import time
from datetime import datetime

py_path = Path(__file__).parent #определяет путь к программе на диске

recent_dbs_sqlite = os.path.join(py_path, "recent_dbs.sqlite")
recent_db_path = {}

def main_menu_close():
    '''закрывает всю программу'''
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
        save_recent_dbs(file_path)
        refresh_listbox()
        current_db_path = file_path
        dictionary_window(file_path)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось создать словарь:\n{e}")

def button_open_database():
    '''кнопка открыть существующий словарь'''
    global current_db_path
    file_path = filedialog.askopenfilename(
        filetypes=[("SQLite Database", "*.db")],
        title="Выберите словарь"
    )
    if file_path:
        try:
            update_last_opened_time(file_path)
            save_recent_dbs(file_path)
            current_db_path = file_path
            refresh_listbox()
            dictionary_window(file_path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть словарь:\n{e}")

def save_recent_dbs(db_path):
    '''сохраняет словари в файл'''
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
    '''информация о создании и открытия словаря'''
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
    '''устанавливает дату создания словаря'''
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
    '''обновляет когда был в последний раз открыт словарь'''
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
    '''получает метадату'''
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

def load_recent_dbs():
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
                cursor.execute("DELETE FROM recent_dbs WHERE path = ?", (path,)) #удаляет недавние базы если их нет
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
        full_path = recent_db_path.get(selected_text) #путь к дата базе на диске
        if full_path:
            current_db_path = full_path #запоминает открытую в данный момент базу данных
            update_last_opened_time(full_path)
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

def show_database_info():
    '''показывает информацию о словаре'''
    selected_index = listbox.curselection()
    if not selected_index:
        messagebox.showerror("Ошибка", "Сначала выберите базу данных!")
        return
    selected_db_path = listbox.get(selected_index)
    metadata = get_metadata(selected_db_path)
    if metadata:
        created_at, last_opened_at = metadata
        db_name = os.path.splitext(os.path.basename(selected_db_path))[0]
        db_path = selected_db_path
        info_text = (
            f"Имя базы данных: {db_name}\n"
            f"Путь: {db_path}\n"
            f"Дата создания: {created_at}\n"
            f"Последнее открытие: {last_opened_at}"
        )
        messagebox.showinfo("Информация о базе данных", info_text)
    else:
        messagebox.showerror("Ошибка", "Не удалось получить информацию о базе данных.")

def button_delete_database():
    '''кнопка удаления словаря'''
    selected = listbox.curselection()
    if not selected:
        messagebox.showwarning("Ошибка", "Выберите словарь для удаления.")
        return
    selected_index = selected[0]
    selected_text = listbox.get(selected_index)
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
            conn = sqlite3.connect(recent_dbs_sqlite)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recent_dbs WHERE path = ?", (db_path,))
            conn.commit()
            conn.close()
            refresh_listbox()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить словарь: {e}")

def show_warning_window(message):
    '''окно предупреждения'''
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
    '''окно словаря'''
    global current_db_path, listbox_words, listbox_translations
    global search_var_words, search_var_translations
    current_db_path = db_path #запоминает базу данных
    main_menu.withdraw()
    dictionary = tk.Toplevel()
    dictionary.title("Словарь")
    screen_width = dictionary.winfo_screenwidth()
    screen_height = dictionary.winfo_screenheight()
    x = (screen_width - 650) // 2
    y = (screen_height - 600) // 2
    dictionary.geometry(f"650x600+{x}+{y}") #размер окна
    dictionary.resizable(True, True)
    def return_to_main_menu():
        '''вернуться в главное меню'''
        dictionary.destroy()
        main_menu.deiconify()
    dictionary.protocol("WM_DELETE_WINDOW", return_to_main_menu)

    dictionary.grid_columnconfigure(0, weight=1)
    dictionary.grid_columnconfigure(1, weight=1)
    dictionary.grid_columnconfigure(2, weight=1)
    dictionary.grid_columnconfigure(3, weight=1)
    dictionary.grid_columnconfigure(4, weight=1)
    dictionary.grid_columnconfigure(5, weight=1)
    dictionary.grid_rowconfigure(3, weight=1)

    def save_word_to_db(db_path, word, translation, part_of_speech):
        '''сохраняет слово в базу данных'''
        if not word or not translation:
            show_warning_window("Введите слово и перевод")
            return
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS words (id INTEGER PRIMARY KEY, word TEXT, translation TEXT, part_of_speech TEXT)")
            cursor.execute("INSERT INTO words (word, translation, part_of_speech) VALUES (?, ?, ?)", (word, translation, part_of_speech))
            conn.commit()
            conn.close()
            refresh_local_word_list()
            messagebox.showinfo("Успешно", "Слово добавлено в словарь")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить слово: {e}")

    #текст
    dictionary_name = os.path.splitext(os.path.basename(db_path))[0]
    dictionary_title = tk.Label(dictionary, text=f"{dictionary_name} словарь", font=("Arial", 14, "bold"))
    dictionary_title.grid(row=0, column=0, columnspan=6, pady=10)

    #кнопка добавить слово в словарь
    def add_word_window(db_path):
        '''окно добавления слова в словарь'''
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
                show_warning_window("Введите слово, перевод или выберите часть речи")
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
        add_window.resizable(False, False)
    button_add_word = ttk.Button(dictionary, text="Добавить слово", command=lambda: add_word_window(db_path))
    button_add_word.grid(row=1, column=0, pady=5, padx=13, ipadx=7, ipady=2, sticky=W)

    def button_delete_selected_word():
        '''кнопка удаления слова'''
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
                refresh_local_word_list()
                messagebox.showinfo("Успешно", f"Слово '{word_to_delete}' удалено.")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить слово: {e}")
    button_delete_word = ttk.Button(dictionary, text="Удалить слово", command=button_delete_selected_word)
    button_delete_word.grid(row=1, column=1, pady=5, padx=25, ipadx=7, ipady=2, sticky=E)

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
        '''фильтрует список переводов по введенному запросу'''
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

    #поле поиска слова
    search_var_words = tk.StringVar()
    search_entry_words = ttk.Entry(dictionary, textvariable=search_var_words, width=30)
    search_entry_words.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
    search_entry_words.bind("<KeyRelease>", filter_words)

    part_of_speech_var = tk.StringVar()
    part_of_speech_combobox = ttk.Combobox(dictionary, textvariable=part_of_speech_var, state="readonly")
    part_of_speech_combobox['values'] = ["", "Существительное", "Глагол", "Прилагательное", "Наречие", "Местоимение", "Предлог", "Союз", "Междометие", "Числительное", "Другое"]
    part_of_speech_combobox.set("")
    part_of_speech_combobox.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
    part_of_speech_combobox.bind("<<ComboboxSelected>>", filter_words)

    search_var_translations = tk.StringVar()
    search_entry_translations = ttk.Entry(dictionary, textvariable=search_var_translations, width=30)
    search_entry_translations.grid(row=2, column=2, columnspan=4, padx=10, pady=10, sticky="ew")
    search_entry_translations.bind("<KeyRelease>", filter_translations)

    #список со словами
    def refresh_local_word_list():
        '''обновляет список со словами'''
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
    def edit_word_window(db_path, listbox_words, listbox_translations):
        '''редактировать слово из списка по двойному нажатию на него'''
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
                refresh_local_word_list()
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
    listbox_words.grid(row=3, column=0, columnspan=2, padx=8, pady=0, sticky=NSEW)
    listbox_words.bind("<Double-Button-1>", lambda event: edit_word_window(db_path, listbox_words, listbox_translations))

    listbox_translations = tk.Listbox(dictionary, height=10, font=("Arial", 12))
    listbox_translations.grid(row=3, column=2, columnspan=4, padx=8, pady=0, sticky=NSEW)
    listbox_translations.bind("<Double-Button-1>", lambda event: edit_word_window(db_path, listbox_words, listbox_translations))

    #кнопка назад в меню
    button_back = ttk.Button(dictionary, text="Назад в меню", command=return_to_main_menu)
    button_back.grid(row=4, column=0, pady=10, ipadx=30, ipady=2, columnspan=6)

    refresh_local_word_list()
    dictionary.mainloop()

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
listbox = tk.Listbox(main_menu, font=("Arial", 13))
listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
listbox.bind("<Double-Button-1>", open_selected_db)
#загружает словари в список
recent_dbs = load_recent_dbs()
for db_path, _ in recent_dbs:
        file_name = os.path.splitext(os.path.basename(db_path))[0]
        recent_db_path[file_name] = db_path
        listbox.insert(tk.END, file_name)

#кнопка информация о словаре
#button_show_info = ttk.Button(main_menu, text="Показать информацию о словаре", command=show_database_info)
#button_show_info.pack(pady=5)

#кнопка удаления
button_delete = ttk.Button(main_menu, text="Удалить словарь", command=button_delete_database)
button_delete.pack(pady=5)

#кнопка закрыть программу
button_programmclose = ttk.Button(main_menu, text="Выйти из программы", command=main_menu_close)
button_programmclose.pack(anchor=S, expand=True, pady=10)

main_menu.update_idletasks()
main_menu.mainloop()
