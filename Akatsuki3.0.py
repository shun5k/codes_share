#決済システムAkatsuki_Ver3.0
#[注意]Ver3.0で全サブプログラムを廃止し本プログラムに統合しました。

#ライブラリのインポート
import tkinter as tk
import csv
import os
import pandas as pd
from tkinter import ttk
import math
from datetime import datetime, timedelta
import subprocess
import json
from time import strftime
import nfc
import threading
from tkinter import font as tkfont
import sys

# 色の定義
BACKGROUND_COLOR = 'gray13'
BUTTON_COLOR = 'midnight blue'
BUTTON_TEXT_COLOR = 'white'
CANCEL_BUTTON_COLOR = 'gray30'
CANCEL_BUTTON_TEXT_COLOR = 'white'
TEXT_COLOR = 'white'  
# フォントサイズを一括で管理
FONT_SIZE = 30

# ファイルパスの定義
csv_file_path = 'NFClist.csv'
log_file_path = 'balance_log.csv'

#NFCタグ登録
def nfc_register():
    def read_balance_from_csv(uid):
        if not os.path.exists(csv_file_path):
            return None, None
        with open(csv_file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file, delimiter=',')
            for row in reader:
                if row['uid'] == uid:
                    return int(row['balance']), row['display_name']
        return None, None

    def write_to_csv(uid, balance, display_name):
        file_exists = os.path.exists(csv_file_path)
        with open(csv_file_path, mode='a', newline='') as file:
            fieldnames = ['uid', 'balance', 'display_name']
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=',')
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({'uid': uid, 'balance': balance, 'display_name': display_name})

    def center_window(root, width, height):
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')

    def ask_display_name():
        root = tk.Tk()
        root.title("新規ユーザー登録")
        root.configure(bg=BACKGROUND_COLOR)
        center_window(root, 700, 300)
        
        default_font =("メイリオ", 25)
        
        tk.Label(root, text="このタグの表示名を入力してください:", font=default_font,bg=BACKGROUND_COLOR,fg=BUTTON_TEXT_COLOR).pack(pady=10)
        display_name_entry = tk.Entry(root, width=30, font=default_font)
        display_name_entry.pack(pady=5)
        
        def on_submit():
            global display_name
            display_name = display_name_entry.get()
            root.destroy()
        
        tk.Button(root, text="登録", command=on_submit, font=default_font).pack(pady=10)
        root.mainloop()
        return display_name

    def show_message(message, next_action=None):
        root = tk.Tk()
        root.title("メッセージ")
        root.configure(bg=BACKGROUND_COLOR)
        center_window(root, 500, 400)
        
        default_font = ("メイリオ", 25)
        
        tk.Label(root, text=message, wraplength=350, font=default_font,bg=BACKGROUND_COLOR, fg=BUTTON_TEXT_COLOR).pack(pady=20)
        
        def on_close():
            root.destroy()
            if next_action:
                next_action()
            else:
                restart_program()  # プログラムを再起動
        
        tk.Button(root, text="閉じる", command=on_close, font=default_font,bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR).pack(pady=10)
        
        root.mainloop()

    def on_connect(tag):
        uid = tag.identifier.hex().upper()
        
        def next_step():
            current_balance, display_name = read_balance_from_csv(uid)
            if current_balance is None:
                display_name = ask_display_name()
                if display_name:
                    write_to_csv(uid, 0, display_name)
                    show_message(f"新しいNFCタグが\n登録されました!\n表示名: {display_name} \n残高: 0円", next_action=restart_program)
            else:
                show_message(f"このタグは既に\n登録されています！\n現在の残高: {current_balance}円\n表示名: {display_name}", next_action=restart_program)
        
        next_step()
        
        return True

    def read_nfc():
        def nfc_thread():
            try:
                with nfc.ContactlessFrontend('usb') as clf:
                    clf.connect(rdwr={'on-connect': on_connect})
            except IOError as e:
                if e.errno == 19:  # ENODEV (No such device)
                    show_message("NFCリーダーを接続して下さい", next_action=restart_program)
        
        threading.Thread(target=nfc_thread, daemon=True).start()

    def restart_program():
        regi_window.destroy()
        # regi()

    def regi():
        global regi_window
        regi_window = tk.Tk()
        regi_window.title("NFCリーダー")
        regi_window.configure(bg=BACKGROUND_COLOR)
        center_window(regi_window, 500, 200)
        
        default_font = tkfont.Font(family="メイリオ", size=30)
        regi_window.option_add("*Font", default_font)
        
        tk.Label(regi_window, text="NFCリーダーに\nタグをかざしてください", wraplength=350, font=default_font,bg=BACKGROUND_COLOR,fg=BUTTON_TEXT_COLOR).pack(pady=20)
        
        read_nfc()
        
        regi_window.mainloop()

    # # CSVファイルを初期化
    # initialize_csv()

    # メインウィンドウを表示してNFCタグを読み取る
    regi()
#チャージ
def add_money():
    def initialize_csv():
        if not os.path.exists(csv_file_path):
            with open(csv_file_path, mode='w', newline='') as file:
                fieldnames = ['uid', 'balance', 'display_name']
                writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=',')
                writer.writeheader()

    def read_csv_to_dict(uid):
        if not os.path.exists(csv_file_path):
            return None
        with open(csv_file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file, delimiter=',')
            for row in reader:
                if row['uid'] == uid:
                    return {'balance': int(row['balance']), 'display_name': row['display_name']}
        return None

    def write_dict_to_csv(uid, balance, display_name):
        file_exists = os.path.exists(csv_file_path)
        rows = []
        if file_exists:
            with open(csv_file_path, mode='r', newline='') as file:
                reader = csv.DictReader(file, delimiter=',')
                for row in reader:
                    rows.append(row)
        
        with open(csv_file_path, mode='w', newline='') as file:
            fieldnames = ['uid', 'balance', 'display_name']
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=',')
            writer.writeheader()
            
            updated = False
            for row in rows:
                if row['uid'] == uid:
                    row['balance'] = balance
                    row['display_name'] = display_name
                    updated = True
                writer.writerow(row)
            
            if not updated:
                writer.writerow({'uid': uid, 'balance': balance, 'display_name': display_name})

    def balancelog_transaction(display_name, fluctuation, new_balance):
        with open(log_file_path, mode='a', newline='') as file:
            fieldnames = ['datetime', 'display_name', 'fluctuation', 'new_balance']
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=',')
            
            if os.stat(log_file_path).st_size == 0:
                writer.writeheader()
            
            writer.writerow({
                'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'display_name': display_name,
                'fluctuation': fluctuation,
                'new_balance': new_balance
            })

    def center_window(root, width, height):
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')

    import sys

    def select_charge(uid, current_balance, display_name):
        management_window = tk.Toplevel()
        management_window.title("金額選択")
        management_window.geometry("500x800")
        management_window.configure(bg=BACKGROUND_COLOR)

        center_window(management_window, 500, 800)

        message = f" {display_name}さん\n現在の残高: {current_balance}円\nチャージ金額を選択"
        tk.Label(management_window, text=message, wraplength=450, bg=BACKGROUND_COLOR, fg=BUTTON_TEXT_COLOR).pack(pady=20)

        main_button_frame = tk.Frame(management_window, bg=BACKGROUND_COLOR)
        main_button_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=20)

        buttons = [
            ("1000円", lambda: add_charge(uid, current_balance, display_name, 1000, management_window)),
            ("2000円", lambda: add_charge(uid, current_balance, display_name, 2000, management_window)),
            ("3000円", lambda: add_charge(uid, current_balance, display_name, 3000, management_window)),
            ("4000円", lambda: add_charge(uid, current_balance, display_name, 4000, management_window)),
            ("5000円", lambda: add_charge(uid, current_balance, display_name, 5000, management_window)),
        ]

        for text, command in buttons:
            button = tk.Button(main_button_frame, text=text, command=command, font=("Arial", 24), bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR)
            button.pack(pady=10, padx=20, fill=tk.X)

        cancel_button_frame = tk.Frame(management_window, bg=BACKGROUND_COLOR)
        cancel_button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        cancel_button = tk.Button(cancel_button_frame, text="キャンセル", command=lambda: close_windows(management_window), font=("Arial", 24), bg=CANCEL_BUTTON_COLOR, fg=CANCEL_BUTTON_TEXT_COLOR)
        cancel_button.pack(side=tk.LEFT, padx=20, pady=10)

    def add_charge(uid, current_balance, display_name, amount, parent_window):
        root = tk.Toplevel(parent_window)
        root.title("チャージ確認")
        center_window(root, 500, 300)
        root.configure(bg=BACKGROUND_COLOR)
        default_font = ("メイリオ", FONT_SIZE)
        
        message = f" {display_name}さん\n現在の残高: {current_balance}円\n{amount}円チャージしますか？"
        tk.Label(root, text=message, wraplength=450, font=default_font, bg=BACKGROUND_COLOR, fg=BUTTON_TEXT_COLOR).pack(pady=20)
        
        def on_ok():
            new_balance = current_balance + amount
            write_dict_to_csv(uid, new_balance, display_name)
            balancelog_transaction(display_name, amount, new_balance)
            show_message(f"{display_name}さん\n{amount}円チャージ\nが完了しました!\nチャージ後の残高: {new_balance}円")
        
        def on_cancel():
            root.destroy()
        
        tk.Button(root, text="キャンセル", command=on_cancel, font=default_font, bg=CANCEL_BUTTON_COLOR, fg=CANCEL_BUTTON_TEXT_COLOR).pack(side=tk.LEFT, padx=20, pady=10)
        tk.Button(root, text="OK", command=on_ok, font=default_font, bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR).pack(side=tk.RIGHT, padx=20, pady=10)

    def show_message(message, next_action=None, auto_close=False, close_delay=2000):
        root = tk.Tk()
        root.title("メッセージ")
        root.configure(bg=BACKGROUND_COLOR)
        center_window(root, 500, 400)
        
        default_font = ("メイリオ", FONT_SIZE)
        
        tk.Label(root, text=message, wraplength=450, font=default_font, bg=BACKGROUND_COLOR, fg=BUTTON_TEXT_COLOR).pack(pady=20)
        
        def on_close():
            sys.exit()
        
        tk.Button(root, text="閉じる", command=on_close, font=default_font, bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR).pack(pady=10)
        
        root.mainloop()

    def close_windows(*windows):
        sys.exit()


    def on_connect(tag):
        uid = tag.identifier.hex().upper()
        data = read_csv_to_dict(uid)
        if (data):
            select_charge(uid, data['balance'], data['display_name'])
        else:
            show_message("このタグは登録されていません。")

    def read_nfc():
        def nfc_thread():
            try:
                with nfc.ContactlessFrontend('usb') as clf:
                    clf.connect(rdwr={'on-connect': on_connect})
            except IOError as e:
                if e.errno == 19:  # ENODEV (No such device)
                    show_message("NFCリーダーを接続して下さい", next_action=restart_program)
        
        threading.Thread(target=nfc_thread, daemon=True).start()


    def restart_program():
        add_money_window.destroy()
        # main()

    def add_money():
        global add_money_window
        add_money_window = tk.Tk()
        add_money_window.title("NFCリーダー")
        add_money_window.configure(bg=BACKGROUND_COLOR)
        center_window(add_money_window, 500, 200)
        
        default_font = ("メイリオ", FONT_SIZE)
        add_money_window.option_add("*Font", default_font)
        
        tk.Label(add_money_window, text="NFCリーダーに\nタグをかざしてください", wraplength=450, font=default_font,bg=BACKGROUND_COLOR,fg=BUTTON_TEXT_COLOR).pack(pady=20)
        
        read_nfc()
        
        add_money_window.mainloop()

    # CSVファイルを初期化
    initialize_csv()

    # メインウィンドウを表示してNFCタグを読み取る
    add_money()
#残高履歴
def check_balance():
    def initialize_csv():
        if not os.path.exists(csv_file_path):
            with open(csv_file_path, mode='w', newline='') as file:
                fieldnames = ['uid', 'balance', 'display_name']
                writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=',')
                writer.writeheader()

    def read_csv_to_dict(uid):
        if not os.path.exists(csv_file_path):
            return None
        with open(csv_file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file, delimiter=',')
            for row in reader:
                if row['uid'] == uid:
                    return {'balance': int(row['balance']), 'display_name': row['display_name']}
        return None

    def write_dict_to_csv(uid, balance, display_name):
        file_exists = os.path.exists(csv_file_path)
        rows = []
        if file_exists:
            with open(csv_file_path, mode='r', newline='') as file:
                reader = csv.DictReader(file, delimiter=',')
                for row in reader:
                    rows.append(row)
        
        with open(csv_file_path, mode='w', newline='') as file:
            fieldnames = ['uid', 'balance', 'display_name']
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=',')
            writer.writeheader()
            
            updated = False
            for row in rows:
                if row['uid'] == uid:
                    row['balance'] = balance
                    row['display_name'] = display_name
                    updated = True
                writer.writerow(row)
            
            if not updated:
                writer.writerow({'uid': uid, 'balance': balance, 'display_name': display_name})

    def center_window(root, width, height):
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')

    def read_balance_log(nfc_display_name):
        if not os.path.exists(log_file_path):
            return "ファイルが見つかりません", None, None

        df = pd.read_csv(log_file_path)

        if 'display_name' not in df.columns:
            return "無効なファイル形式です", None, None

        filtered_df = df[df['display_name'] == nfc_display_name]

        if filtered_df.empty:
            return "データが見つかりません", None, None

        filtered_df['datetime'] = pd.to_datetime(filtered_df['datetime'])
        
        filtered_df = filtered_df.sort_values('datetime', ascending=False)

        return "成功", filtered_df, None

    def update_view(period, data, tree):
        tree.delete(*tree.get_children())
        if period == '履歴':
            for _, row in data.sort_values('datetime', ascending=True).iterrows():
                if row['fluctuation'] < 0:
                    tree.insert('', '0', values=(row['datetime'], f"{abs(row['fluctuation']):,}円", ""))
                elif row['fluctuation'] > 0:
                    tree.insert('', '0', values=(row['datetime'], "", f"{row['fluctuation']:,}円"))
        elif period == '全期間':
            purchases = data[data['fluctuation'] < 0]['fluctuation'].sum()
            purchases = - purchases
            charges = data[data['fluctuation'] > 0]['fluctuation'].sum()
            tree.insert('', '0', values=('全期間', 
                                        f"{purchases:,}円 ", 
                                        f"{charges:,}円"))
        else:
            grouped = data.groupby(pd.Grouper(key='datetime', freq={'年別': 'Y', '月別': 'M', '日別': 'D'}[period]))
            for name, group in sorted(grouped, key=lambda x: x[0], reverse=False):
                if not group.empty:
                    purchases = group[group['fluctuation'] < 0]['fluctuation'].sum()
                    purchases = - purchases
                    charges = group[group['fluctuation'] > 0]['fluctuation'].sum()
                    
                    if period == '年別':
                        date_display = name.strftime('%Y')
                    elif period == '月別':
                        date_display = name.strftime('%Y-%m')
                    else:
                        date_display = name.strftime('%Y-%m-%d')

                    tree.insert('', '0', values=(date_display, 
                                                f"{purchases:,}円 ", 
                                                f"{charges:,}円"))

    def confirm_charge(uid, current_balance, display_name):
        status, data, _ = read_balance_log(display_name)
        
        if status != "成功":
            show_message(status)
            return
        cb_window.destroy
        root = tk.Tk()
        root.title("残高履歴")
        root.configure(bg=BACKGROUND_COLOR)
        center_window(root, 1200, 800)

        default_font = ("メイリオ", FONT_SIZE)

        # 残高表示を画面の一番上に追加
        balance_label = tk.Label(root, text=f"{display_name}さんの残高は{current_balance}円です", font=default_font, bg=BACKGROUND_COLOR, fg=BUTTON_TEXT_COLOR)
        balance_label.pack(pady=(10, 0))

        frame = tk.Frame(root, bg=BACKGROUND_COLOR)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        style = ttk.Style(root)
        style.theme_use("clam")
        style.configure("Treeview", 
                    rowheight=50,
                    font=("メイリオ", 30), 
                    background="gray13", 
                    foreground="white", 
                    fieldbackground="gray13")
        style.configure("Treeview.Heading", 
                        background="gray13", 
                        foreground=BUTTON_TEXT_COLOR, 
                        font=("メイリオ", 30))
        style.map('Treeview', background=[('selected', BUTTON_COLOR)])
        
        tree = ttk.Treeview(frame, columns=('日時', '購入', 'チャージ'), show='headings', height=10)
        tree.heading('日時', text='日時')
        tree.heading('購入', text='購入')
        tree.heading('チャージ', text='チャージ')
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tree.column('日時', width=400)
        tree.column('購入', width=250)
        tree.column('チャージ', width=250)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)

        button_frame = tk.Frame(root, bg=BACKGROUND_COLOR)
        button_frame.pack(fill=tk.X, padx=20, pady=10)

        # ボタンをグリッドで配置
        periods = ['履歴', '全期間', '年別', '月別', '日別']
        for i, period in enumerate(periods):
            tk.Button(button_frame, text=period, command=lambda p=period: update_view(p, data, tree), 
                    font=("メイリオ", 20), bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR).grid(row=0, column=i, padx=5)
            
        # 閉じるボタンを右端に配置
        close_button = tk.Button(button_frame, text="閉じる", command=root.destroy, font=("メイリオ", 20), 
                                bg=CANCEL_BUTTON_COLOR, fg=CANCEL_BUTTON_TEXT_COLOR)
        close_button.grid(row=0, column=len(periods), padx=5, sticky='e')

        # Configure the grid to stretch the last column (close button) to the right
        button_frame.columnconfigure(len(periods), weight=1)
        root.mainloop()

    def show_message(message, next_action=None):
        root = tk.Tk()
        root.title("メッセージ")
        root.configure(bg=BACKGROUND_COLOR)
        center_window(root, 500, 300)
        
        default_font = ("メイリオ", FONT_SIZE)
        
        tk.Label(root, text=message, wraplength=450, font=default_font, bg=BACKGROUND_COLOR, fg=BUTTON_TEXT_COLOR).pack(pady=20)
        
        def on_close():
            root.destroy()
            cb_window.destroy()
        
        tk.Button(root, text="閉じる", command=on_close, font=default_font,bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR).pack(pady=10)
        
        root.mainloop()

    def on_connect(tag):
        uid = tag.identifier.hex().upper()
        data = read_csv_to_dict(uid)
        if data:
            cb_window.destroy()  # NFCタグを読み取ったらウィンドウを閉じる
            confirm_charge(uid, data['balance'], data['display_name'])
        else:
            cb_window.destroy()  # NFCタグを読み取ったらウィンドウを閉じる
            show_message("このタグは\n登録されていません")
        
    def read_nfc():
        def nfc_thread():
            try:
                with nfc.ContactlessFrontend('usb') as clf:
                    clf.connect(rdwr={'on-connect': on_connect})
            except IOError as e:
                if e.errno == 19:  # ENODEV (No such device)
                    show_message("NFCリーダーを接続して下さい")
        
        threading.Thread(target=nfc_thread, daemon=True).start()


    def cb():
        global cb_window
        cb_window = tk.Tk()
        cb_window.title("NFCリーダー")
        cb_window.configure(bg=BACKGROUND_COLOR)
        center_window(cb_window, 500, 200)
        
        default_font = ("メイリオ", FONT_SIZE)
        cb_window.option_add("*Font", default_font)
        
        tk.Label(cb_window, text="NFCリーダーに\nタグをかざしてください", wraplength=450, font=default_font,bg=BACKGROUND_COLOR, fg=BUTTON_TEXT_COLOR).pack(pady=20)
        
        read_nfc()
        
        cb_window.mainloop()

    # CSVファイルを初期化
    initialize_csv()

    # メインウィンドウを表示してNFCタグを読み取る
    cb()
#メイン処理
def main():

    # 商品名を改行付きでフォーマットする関数
    def format_button_name(name):
        words = name.split()
        return "\n".join(words)

    #商品リスト読み込み
    def load_csv(file_name):
        button_names = []
        amounts = []
        with open(file_name, 'r', encoding='UTF-8') as file:
            csv_reader = csv.reader(file, delimiter=',')
            for i, row in enumerate(csv_reader):
                if i >= 1:  # 2行目から読み込み
                    if len(row) >= 2:
                        formatted_name = format_button_name(row[0])
                        button_names.append(formatted_name)
                        amounts.append(int(row[1]))
        return button_names, amounts

    #合計個数、合計金額
    def update_total_labels(tabs_data, total_count_label, total_amount_label):
        total_counts = 0
        total_amounts = 0
        
        for tab in tabs_data.values():
            counts = tab['counts']
            amounts = tab['amounts']
            
            total_counts += sum(counts)
            total_amounts += sum(counts[i] * amounts[i] for i in range(len(counts)))
            
        
        total_count_label.config(text=f"合計個数: {total_counts}個", font=("Arial", 24), fg=TEXT_COLOR)
        total_amount_label.config(text=f"合計金額: {total_amounts}円", font=("Arial", 24), fg=TEXT_COLOR)
        
    # 各タブのCSVファイルを読み込む
    snack_button_names, snack_amounts = load_csv('Snack_list.csv')
    colddrink_button_names, colddrink_amounts = load_csv('Cold_drink_list.csv')
    hotdrink_button_names, hotdrink_amounts = load_csv('Hot_drink_list.csv')
    food_button_names, food_amounts = load_csv('Food_list.csv')
    ice_button_names, ice_amounts = load_csv('Icecream_list.csv')



    #商品名、+-ボタンを押したときの処理
    def update_count(button_number, increment, counts, count_labels, total_count_label, total_amount_label, amounts, tabs_data):
        counts[button_number] += increment
        if counts[button_number] < 0:
            counts[button_number] = 0
        update_labels(counts, count_labels)
        update_total_labels(tabs_data, total_count_label, total_amount_label)

    def update_labels(counts, count_labels):
        for i, label in enumerate(count_labels):
            label.config(text=f"{counts[i]}個", font=("Arial", 18), fg=TEXT_COLOR)

    def reset_counts(tabs_data, total_count_label, total_amount_label):
        for tab in tabs_data.values():
            counts = tab['counts']
            count_labels = tab['count_labels']
            for i in range(len(counts)):
                counts[i] = 0  # カウントを0にリセット
                count_labels[i].config(text=f"0個", font=("Arial", 18), fg=TEXT_COLOR)  # ラベルもリセット
        update_total_labels(tabs_data, total_count_label, total_amount_label) 
    #販売履歴書き込み
    def log_transaction(summary_text):
        with open('log.csv', 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow([now])
            writer.writerow([summary_text])
    # #決済処理

    # def run_payment_and_reset(total_amount, summary_text):
    #     payment_output = run_payment_processing_program(total_amount)
    #     if payment_output == "COMPLETE":
    #         log_transaction(summary_text)
    #         reset_counts(tabs_data, total_count_label, total_amount_label)
    #     return payment_output

    # def run_payment_processing_program(total_amount):
    #     args = ["python", "payment_processing.py", str(total_amount)]
    #     result = subprocess.run(args, capture_output=True, text=True, check=True)
    #     output = result.stdout.strip()
    #     return output


    # def run_payment_stera_and_reset(total_amount, summary_text):
    #     payment_output = run_payment_processing_stera_program(total_amount)
    #     if payment_output == "COMPLETE":
    #         log_transaction(summary_text)
    #         reset_counts(tabs_data, total_count_label, total_amount_label)
    #     return payment_output

    # def run_payment_processing_stera_program(total_amount):
    #     args = ["python", "payment_processing_stera.py", str(total_amount)]
    #     result = subprocess.run(args, capture_output=True, text=True, check=True)
    #     output = result.stdout.strip()
    #     return output


    #管理画面
    def management():
        management_window = tk.Toplevel(win)
        management_window.title("管理")
        management_window.geometry("500x800")
        management_window.configure(bg=BACKGROUND_COLOR)

        # ウィンドウを中央に配置
        management_window.update_idletasks()
        width = management_window.winfo_width()
        height = management_window.winfo_height()
        x = (management_window.winfo_screenwidth() // 2) - (width // 2)
        y = (management_window.winfo_screenheight() // 2) - (height // 2)
        management_window.geometry(f'{width}x{height}+{x}+{y}')


        # def run_NFCregister_program():
        #     subprocess.run(["python", "NFCregister.py"])

        # メインボタンフレーム（上部）
        main_button_frame = tk.Frame(management_window, bg=BACKGROUND_COLOR)
        main_button_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=20)

        # ボタンを上から順に配置
        buttons = [
            ("販売履歴", show_history),
            ("残高履歴", show_balance_history),
            ("集計", run_aggregate_program),
            ("NFCタグ登録",nfc_register),
            ("アプリ終了", run_shutdown_program)

            
        ]

        for text, command in buttons:
            button = tk.Button(main_button_frame, text=text, command=command, font=("Arial", 24), bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR)
            button.pack(pady=10, padx=20, fill=tk.X)

        


        # キャンセルボタンフレーム（下部）
        cancel_button_frame = tk.Frame(management_window, bg=BACKGROUND_COLOR)
        cancel_button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        cancel_button = tk.Button(cancel_button_frame, text="キャンセル", command=management_window.destroy, font=("Arial", 24), bg=CANCEL_BUTTON_COLOR, fg=CANCEL_BUTTON_TEXT_COLOR)
        cancel_button.pack(side=tk.LEFT, padx=20, pady=10)

    #購入確認画面
    def show_summary():
        summary_window = tk.Toplevel(win)
        summary_window.title("確認画面")
        summary_window.geometry("800x700")
        summary_window.configure(bg=BACKGROUND_COLOR)

        # ウィンドウを中央に配置
        summary_window.update_idletasks()
        width = summary_window.winfo_width()
        height = summary_window.winfo_height()
        x = (summary_window.winfo_screenwidth() // 2) - (width // 2)
        y = (summary_window.winfo_screenheight() // 2) - (height // 2)
        summary_window.geometry(f'{width}x{height}+{x}+{y}')

        # 商品リストを表示するフレーム
        list_frame = tk.Frame(summary_window, bg=BACKGROUND_COLOR)
        list_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

        # ヘッダー
        tk.Label(list_frame, text="商品名", font=("Arial", 40, "bold"), bg=BACKGROUND_COLOR, fg=TEXT_COLOR, anchor='w').grid(row=0, column=0, sticky='w', padx=(0,20))
        tk.Label(list_frame, text="金額", font=("Arial", 40, "bold"), bg=BACKGROUND_COLOR, fg=TEXT_COLOR, anchor='e').grid(row=0, column=1, sticky='e', padx=(0,20))
        tk.Label(list_frame, text="個数", font=("Arial", 40, "bold"), bg=BACKGROUND_COLOR, fg=TEXT_COLOR, anchor='e').grid(row=0, column=2, sticky='e')
        
        
        summary_text = "\n商品名\t金額\t個数\n"
        # 各タブの合計を計算し表示
        row = 1
        total_counts = 0
        total_amounts = 0
    
        for tab_name, tab in tabs_data.items():
            counts = tab['counts']
            amounts = tab['amounts']
            button_names = tab['button_names']
            tab_total_counts = sum(counts)
            tab_total_amounts = sum(counts[i] * amounts[i] for i in range(len(counts)))
        
            for i in range(len(button_names)):
                if counts[i] > 0:
                    tk.Label(list_frame, text=button_names[i], font=("Arial", 36), bg=BACKGROUND_COLOR, fg=TEXT_COLOR, anchor='w').grid(row=row, column=0, sticky='w', padx=(0,20))
                    tk.Label(list_frame, text=f"{amounts[i]}円", font=("Arial", 36), bg=BACKGROUND_COLOR, fg=TEXT_COLOR, anchor='e').grid(row=row, column=1, sticky='e', padx=(0,20))
                    tk.Label(list_frame, text=f"{counts[i]}個", font=("Arial", 36), bg=BACKGROUND_COLOR, fg=TEXT_COLOR, anchor='e').grid(row=row, column=2, sticky='e')
                    summary_text += f"{button_names[i]}\t{amounts[i]}円\t{counts[i]}個\n"
                    row += 1
            total_counts += tab_total_counts
            total_amounts += tab_total_amounts

    
        # 全体の合計を表示
        tk.Label(list_frame, text="合計", font=("Arial", 40, "bold"), bg=BACKGROUND_COLOR, fg=TEXT_COLOR, anchor='w').grid(row=row, column=0, sticky='w', pady=(10,0))
        tk.Label(list_frame, text=f"{total_amounts}円", font=("Arial", 40, "bold"), bg=BACKGROUND_COLOR, fg=TEXT_COLOR, anchor='e').grid(row=row, column=1, sticky='e', pady=(10,0), padx=(0,20))
        tk.Label(list_frame, text=f"{total_counts}個", font=("Arial", 40, "bold"), bg=BACKGROUND_COLOR, fg=TEXT_COLOR, anchor='e').grid(row=row, column=2, sticky='e', pady=(10,0))

        summary_text += f"\n合計個数: {total_counts}個\n合計金額: {total_amounts}円\n"
    
    
        # ボタン
        button_frame = tk.Frame(summary_window, bg=BACKGROUND_COLOR)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        cancel_button = tk.Button(button_frame, text="キャンセル", command=summary_window.destroy, font=("Arial", 24), bg=CANCEL_BUTTON_COLOR, fg=CANCEL_BUTTON_TEXT_COLOR)
        cancel_button.pack(side=tk.LEFT, padx=20)

        confirm_button = tk.Button(button_frame, text="プリペイド", command=lambda: [summary_window.destroy(), payment_processing(total_amounts,summary_text)], font=("Arial", 24), bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR)
        confirm_button.pack(side=tk.RIGHT, padx=20)

        alt_button = tk.Button(button_frame, text="クレジット", command=lambda: [summary_window.destroy(),payment_processing_alt(total_amounts,summary_text) ], font=("Arial", 24), bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR)
        alt_button.pack(side=tk.RIGHT, padx=20)

        return total_amounts
    #プリペイド決済処理
    def payment_processing(total_amounts,summary_text):
        # # 合計金額
        total_amount = total_amounts
        # 許容される最大残高不足
        MAX_OVERDRAFT = 1500
        def initialize_csv():
            if not os.path.exists(csv_file_path):
                with open(csv_file_path, mode='w', newline='') as file:
                    fieldnames = ['uid', 'balance', 'display_name']
                    writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=',')
                    writer.writeheader()

        def read_csv_to_dict(uid):
            if not os.path.exists(csv_file_path):
                return None
            with open(csv_file_path, mode='r', newline='') as file:
                reader = csv.DictReader(file, delimiter=',')
                for row in reader:
                    if row['uid'] == uid:
                        return {'balance': int(row['balance']), 'display_name': row['display_name']}
            return None

        def write_dict_to_csv(uid, balance, display_name):
            file_exists = os.path.exists(csv_file_path)
            rows = []
            if file_exists:
                with open(csv_file_path, mode='r', newline='') as file:
                    reader = csv.DictReader(file, delimiter=',')
                    for row in reader:
                        rows.append(row)
            
            with open(csv_file_path, mode='w', newline='') as file:
                fieldnames = ['uid', 'balance', 'display_name']
                writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=',')
                writer.writeheader()
                
                updated = False
                for row in rows:
                    if row['uid'] == uid:
                        row['balance'] = balance
                        row['display_name'] = display_name
                        updated = True
                    writer.writerow(row)
                
                if not updated:
                    writer.writerow({'uid': uid, 'balance': balance, 'display_name': display_name})

        def balancelog_transaction(display_name, total_amount, new_balance):
            with open(log_file_path, mode='a', newline='') as file:
                fieldnames = ['datetime', 'display_name', 'total_amount', 'new_balance']
                writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=',')
                
                if os.stat(log_file_path).st_size == 0:
                    writer.writeheader()
                
                writer.writerow({
                    'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'display_name': display_name,
                    'total_amount': -total_amount,
                    'new_balance': new_balance
                })

        def center_window(root, width, height):
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            root.geometry(f'{width}x{height}+{x}+{y}')

        def show_message(message, next_action=None, auto_close=False, close_delay=2000):
            root = tk.Tk()
            root.title("メッセージ")
            root.configure(bg=BACKGROUND_COLOR)
            center_window(root, 500, 300)
            
            default_font = ("メイリオ", 25)
            
            tk.Label(root, text=message, wraplength=350, font=default_font,bg=BACKGROUND_COLOR, fg=BUTTON_TEXT_COLOR).pack(pady=20)
            
            def on_close():
                root.destroy()
                if next_action:
                    next_action()
                else:
                    restart_program()  # プログラムを再起動
            
            tk.Button(root, text="閉じる", command=on_close, font=default_font).pack(pady=10)
            
            root.mainloop()

        def on_connect(tag):
            uid = tag.identifier.hex().upper()
            data = read_csv_to_dict(uid)
            if data:
                current_balance = data['balance']  # ここで辞書から残高を取り出す
                new_balance = current_balance - total_amount

                if new_balance < -MAX_OVERDRAFT:
                    show_message(f"残高が不足しています!\n現在の残高: {current_balance}円")
                    return True

                write_dict_to_csv(uid, new_balance, data['display_name'])
                balancelog_transaction(data['display_name'], total_amount, new_balance)
                # print("COMPLETE")
                balancelog_transaction(data['display_name'], total_amount, new_balance)
                log_transaction(summary_text)
                show_message(f"決済が完了しました。\n購入金額: {total_amount}円\n新しい残高: {new_balance}円")
                reset_counts(tabs_data, total_count_label, total_amount_label)

                

            else:
                show_message("このタグは登録されていません。")

            return True

        def read_nfc():
            def nfc_thread():
                try:
                    with nfc.ContactlessFrontend('usb') as clf:
                        clf.connect(rdwr={'on-connect': on_connect})
                except IOError as e:
                    if e.errno == 19:  # ENODEV (No such device)
                        show_message("NFCリーダーを接続して下さい", next_action=restart_program)
            
            threading.Thread(target=nfc_thread, daemon=True).start()

        def restart_program():
            payment_window.destroy()
            # main()

        def payment():
            global payment_window
            payment_window = tk.Tk()
            payment_window.title("NFCリーダー")
            payment_window.configure(bg=BACKGROUND_COLOR)
            center_window(payment_window, 500, 200)
            
            default_font = ("メイリオ", FONT_SIZE)
            payment_window.option_add("*Font", default_font)
            
            tk.Label(payment_window, text="NFCリーダーに\nタグをかざしてください", wraplength=450, font=default_font,bg=BACKGROUND_COLOR,fg=BUTTON_TEXT_COLOR).pack(pady=20)
            
            read_nfc()
            
            payment_window.mainloop()

        # CSVファイルを初期化
        initialize_csv()

        # メインウィンドウを表示してNFCタグを読み取る
        payment()
    #外部決済
    def payment_processing_alt(total_amounts,summary_text):
        # 合計金額
        total_amount = total_amounts
        def initialize_csv():
            if not os.path.exists(csv_file_path):
                with open(csv_file_path, mode='w', newline='') as file:
                    fieldnames = ['uid', 'balance', 'display_name']
                    writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=',')
                    writer.writeheader()

        def read_csv_to_dict(uid):
            if not os.path.exists(csv_file_path):
                return None
            with open(csv_file_path, mode='r', newline='') as file:
                reader = csv.DictReader(file, delimiter=',')
                for row in reader:
                    if row['uid'] == uid:
                        return {'balance': int(row['balance']), 'display_name': row['display_name']}
            return None

        def write_dict_to_csv(uid, balance, display_name):
            file_exists = os.path.exists(csv_file_path)
            rows = []
            if file_exists:
                with open(csv_file_path, mode='r', newline='') as file:
                    reader = csv.DictReader(file, delimiter=',')
                    for row in reader:
                        rows.append(row)
            
            with open(csv_file_path, mode='w', newline='') as file:
                fieldnames = ['uid', 'balance', 'display_name']
                writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=',')
                writer.writeheader()
                
                updated = False
                for row in rows:
                    if row['uid'] == uid:
                        row['balance'] = balance
                        row['display_name'] = display_name
                        updated = True
                    writer.writerow(row)
                
                if not updated:
                    writer.writerow({'uid': uid, 'balance': balance, 'display_name': display_name})

        def balancelog_transaction(display_name, total_amount, new_balance):
            with open(log_file_path, mode='a', newline='') as file:
                fieldnames = ['datetime', 'display_name', 'total_amount', 'new_balance']
                writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=',')
                
                if os.stat(log_file_path).st_size == 0:
                    writer.writeheader()
                
                writer.writerow({
                    'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'display_name': display_name,
                    'total_amount': -total_amount,
                    'new_balance': new_balance
                })

        def center_window(root, width, height):
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            root.geometry(f'{width}x{height}+{x}+{y}')


        def alt_complete():
                alt_window.destroy()
                uid = '4ACD0D40'
                data = read_csv_to_dict(uid)
                if data:
                    current_balance = data['balance']  
                    new_balance = current_balance - total_amount

                    write_dict_to_csv(uid, new_balance, data['display_name'])
                    balancelog_transaction(data['display_name'], total_amount, new_balance)
                    # print("COMPLETE")
                    log_transaction(summary_text)
                    reset_counts(tabs_data, total_count_label, total_amount_label)


        def alt():
            global alt_window
            alt_window = tk.Tk()
            alt_window.title("クレジット決済")
            alt_window.configure(bg=BACKGROUND_COLOR)
            center_window(alt_window, 1200, 700)
            
            default_font = ("メイリオ", FONT_SIZE)
            alt_window.option_add("*Font", default_font)
            
            tk.Label(alt_window, text=f"合計金額は{total_amount}円です\n\nVISA・Mastercardのタッチ決済のみ利用可能です\n右側の決済端末を操作してください⇒⇒⇒\n①電源ボタン（右側面）を押す\n②「タッチ決済」を選択\n③金額({total_amount}円)を入力して「次へ」\n③カード・スマホを決済端末背面（🛜）にかざす\n④↘「支払い完了」ボタンを押す", font=default_font,bg=BACKGROUND_COLOR,fg=BUTTON_TEXT_COLOR).pack(pady=20)
            
            button_frame = tk.Frame(alt_window, bg=BACKGROUND_COLOR)
            button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
            
            back_button = tk.Button(button_frame, text="戻る", command=alt_window.destroy, font=default_font,bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR)
            back_button.pack(side=tk.LEFT, padx=20)
            
            complete_button = tk.Button(button_frame, text="支払い完了", command=alt_complete, font=default_font,bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR)
            complete_button.pack(side=tk.RIGHT, padx=20)
            
            alt_window.mainloop()

        # CSVファイルを初期化
        initialize_csv()

        # メインウィンドウを表示してNFCタグを読み取る
        alt()

    #販売履歴表示
    def show_history():
        history_window = tk.Toplevel()
        history_window.title("取引履歴")
        history_window.geometry("800x600")
        history_window.configure(bg=BACKGROUND_COLOR)

        # ウィンドウを中央に配置
        history_window.update_idletasks()
        width = history_window.winfo_width()
        height = history_window.winfo_height()
        x = (history_window.winfo_screenwidth() // 2) - (width // 2)
        y = (history_window.winfo_screenheight() // 2) - (height // 2)
        history_window.geometry(f'{width}x{height}+{x}+{y}')

        # スクロール可能なテキストウィジェットを作成
        text_widget = tk.Text(history_window, wrap=tk.WORD, bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Arial", 22))
        text_widget.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # スクロールバーを追加
        scrollbar = tk.Scrollbar(text_widget)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text_widget.yview)

        try:
            with open('log.csv', 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                logs = list(reader)
                logs.reverse()  # 最新のものから表示するために逆順にする

                for i in range(0, len(logs), 2):  # 2行ごとのデータを処理
                    if i + 1 < len(logs):
                        date_time = logs[i+1][0]
                        transaction = logs[i][0]
                        # 引用符を取り除く
                        transaction = transaction.strip('"')
                        text_widget.insert(tk.END, f"日時: {date_time}\n")
                        text_widget.insert(tk.END, f"取引内容:\n{transaction}\n")
                        text_widget.insert(tk.END, "-" * 50 + "\n")
        except FileNotFoundError:
            text_widget.insert(tk.END, "履歴がありません。")

        text_widget.config(state=tk.DISABLED)  # テキストを読み取り専用にする


    #残高履歴表示
    def show_balance_history():
        balance_history_window = tk.Toplevel(win)
        balance_history_window.title("取引履歴")
        balance_history_window.geometry("800x600")
        balance_history_window.configure(bg=BACKGROUND_COLOR)

        # ウィンドウを中央に配置
        balance_history_window.update_idletasks()
        width = balance_history_window.winfo_width()
        height = balance_history_window.winfo_height()
        x = (balance_history_window.winfo_screenwidth() // 2) - (width // 2)
        y = (balance_history_window.winfo_screenheight() // 2) - (height // 2)
        balance_history_window.geometry(f'{width}x{height}+{x}+{y}')

        # スクロール可能なテキストウィジェットを作成
        text_widget = tk.Text(balance_history_window, wrap=tk.WORD, bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Arial", 22))
        text_widget.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

        # スクロールバーを追加
        scrollbar = tk.Scrollbar(text_widget)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=text_widget.yview)

        try:
            with open('balance_log.csv', 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                logs = list(reader)
                logs.reverse()  # 最新のものから表示するために逆順にする

                for log in logs:
                    if len(log) >= 2:
                        date_time, display_name, fluctuation, new_balance = log[0], log[1],log[2],log[3]
                        text_widget.insert(tk.END, f"日時: {date_time}\n")
                        text_widget.insert(tk.END, f"表示名:{display_name}\n")
                        text_widget.insert(tk.END, f"変動:{fluctuation}\n")
                        text_widget.insert(tk.END, f"新しい残高:{new_balance}\n")
                        text_widget.insert(tk.END, "-" * 50 + "\n")
        except FileNotFoundError:
            text_widget.insert(tk.END, "履歴がありません。")

        text_widget.config(state=tk.DISABLED)  # テキストを読み取り専用にする
    def run_aggregate_program():#集計処理
        FONT_SIZE = 30
        
        csv_file_path = 'NFClist.csv'
        balance_log_path = 'balance_log.csv'

        def initialize_csv():
            if not os.path.exists(csv_file_path):
                with open(csv_file_path, mode='w', newline='') as file:
                    fieldnames = ['uid', 'balance', 'display_name']
                    writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=',')
                    writer.writeheader()

        def read_csv_to_dict():
            """CSVファイルの全データをリスト形式で返す"""
            if not os.path.exists(csv_file_path):
                return []
            with open(csv_file_path, mode='r', newline='') as file:
                reader = csv.DictReader(file, delimiter=',')
                return [row for row in reader]

        def write_dict_to_csv(data):
            """リスト形式のデータをCSVファイルに書き込む"""
            with open(csv_file_path, mode='w', newline='') as file:
                fieldnames = ['uid', 'balance', 'display_name']
                writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=',')
                writer.writeheader()
                writer.writerows(data)

        def center_window(root, width, height):
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            root.geometry(f'{width}x{height}+{x}+{y}')

        def read_balance_log():
            """UIDに関係なく全データを取得"""
            if not os.path.exists(balance_log_path):
                return "ファイルが見つかりません", None

            df = pd.read_csv(balance_log_path)

            if 'display_name' not in df.columns:
                return "無効なファイル形式です", None

            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.sort_values('datetime', ascending=False)

            return "成功", df

        def update_view(period, data, tree):
            tree.delete(*tree.get_children())
            if period == '履歴':
                for _, row in data.sort_values('datetime', ascending=True).iterrows():
                    if row['fluctuation'] < 0:
                        tree.insert('', '0', values=(row['datetime'], f"{abs(row['fluctuation']):,}円", ""))
                    elif row['fluctuation'] > 0:
                        tree.insert('', '0', values=(row['datetime'], "", f"{row['fluctuation']:,}円"))
            elif period == '全期間':
                purchases = data[data['fluctuation'] < 0]['fluctuation'].sum()
                purchases = -purchases
                charges = data[data['fluctuation'] > 0]['fluctuation'].sum()
                tree.insert('', '0', values=('全期間',
                                            f"{purchases:,}円 ",
                                            f"{charges:,}円"))
            else:
                grouped = data.groupby(pd.Grouper(key='datetime', freq={'年別': 'Y', '月別': 'M', '日別': 'D'}[period]))
                for name, group in sorted(grouped, key=lambda x: x[0], reverse=False):
                    if not group.empty:
                        purchases = group[group['fluctuation'] < 0]['fluctuation'].sum()
                        purchases = -purchases
                        charges = group[group['fluctuation'] > 0]['fluctuation'].sum()

                        if period == '年別':
                            date_display = name.strftime('%Y')
                        elif period == '月別':
                            date_display = name.strftime('%Y-%m')
                        else:
                            date_display = name.strftime('%Y-%m-%d')

                        tree.insert('', '0', values=(date_display,
                                                    f"{purchases:,}円 ",
                                                    f"{charges:,}円"))

        def aggregate():
            status, data = read_balance_log()

            if status != "成功":
                show_message(status)
                return

            root = tk.Tk()
            root.title("残高履歴")
            root.configure(bg="gray13")
            center_window(root, 1200, 800)

            default_font = ("メイリオ", FONT_SIZE)

            frame = tk.Frame(root, bg="gray13")
            frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            style = ttk.Style(root)
            style.theme_use("clam")
            style.configure("Treeview",
                            rowheight=50,
                            font=("メイリオ", 30),
                            background="gray13",
                            foreground="white",
                            fieldbackground="gray13")
            style.configure("Treeview.Heading",
                            background="gray13",
                            foreground="white",
                            font=("メイリオ", 30))
            
            tree = ttk.Treeview(frame, columns=('日時', '購入', 'チャージ'), show='headings', height=10)
            tree.heading('日時', text='日時')
            tree.heading('購入', text='購入')
            tree.heading('チャージ', text='チャージ')
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            tree.column('日時', width=400)
            tree.column('購入', width=250)
            tree.column('チャージ', width=250)

            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            button_frame = tk.Frame(root, bg="gray13")
            button_frame.pack(fill=tk.X, padx=20, pady=10)

            periods = ['履歴', '全期間', '年別', '月別', '日別']
            
            for i, period in enumerate(periods):
                tk.Button(button_frame,
                        text=period,
                        command=lambda p=period: update_view(p, data, tree),
                        font=("メイリオ", 20),
                        bg="midnight blue",
                        fg="white").grid(row=0, column=i, padx=5)

        initialize_csv()
        
        # 集計処理の実行
        aggregate()

    def run_shutdown_program():
        win.destroy()

        
    # def run_check_balannce_program():
    #         subprocess.run(["python", "Check_Balance.py"])

    #メインウィンドウを作成
    win = tk.Tk()
    win.title("POS")
    win.configure(bg=BACKGROUND_COLOR)

    # フルスクリーンモードに設定
    win.attributes('-fullscreen', True)
    #win.geometry(f"1500x700")


    #メインウィンドウの中身を作成
    #タブの実装
    # スタイルの設定
    style = ttk.Style()
    style.theme_use('default')
    style.configure('TNotebook', background=BACKGROUND_COLOR)
    style.configure('TNotebook.Tab', font=('Arial', 25), foreground='blue', background=BACKGROUND_COLOR, padding=[100, 10])
    style.map('TNotebook.Tab', background=[('selected', BACKGROUND_COLOR), ('!selected', 'gray30')], foreground=[('selected', 'white'), ('!selected', 'white')])

    # タブを作成するためのNotebookウィジェット
    tab = ttk.Notebook(win)
    tab.pack(fill='both', expand=True)

    # 各タブのデータを保持するためのリスト
    tabs_data = {
        'Food': {'button_names': food_button_names, 'amounts': food_amounts},
        'Snack': {'button_names': snack_button_names, 'amounts': snack_amounts},
        'Hot': {'button_names': hotdrink_button_names, 'amounts': hotdrink_amounts},  
        'Cold': {'button_names': colddrink_button_names, 'amounts': colddrink_amounts},
        'Ice': {'button_names': ice_button_names, 'amounts': ice_amounts}

    }


    # 各タブの初期化
    for tab_name, data in tabs_data.items():
        # 各タブのフレームを作成
        frame = ttk.Frame(tab)
        tab.add(frame, text=tab_name)
        
        # 各タブのデータを取得
        button_names = data['button_names']
        amounts = data['amounts']
        counts = [0] * len(button_names)  # 各タブごとにcountsを初期化

        # 商品、+-ボタンの配置
        main_frame = tk.Frame(frame, bg=BACKGROUND_COLOR)
        main_frame.pack(expand=True, fill=tk.BOTH)

        rows = math.ceil(len(button_names) / 6)
        for i in range(rows):
            main_frame.grid_rowconfigure(i, weight=1)
        for i in range(6):
            main_frame.grid_columnconfigure(i, weight=1)

        count_labels = []

        for i in range(len(button_names)):
            row = i // 6
            col = i % 6

            item_frame = tk.Frame(main_frame, bg=BACKGROUND_COLOR)
            item_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            main_button = tk.Button(item_frame, text=f"{button_names[i]}\n{amounts[i]}円", width=10, height=3, command=lambda x=i, c=counts, cl=count_labels, a=amounts: update_count(x, 1, c, cl, total_count_label, total_amount_label, a, tabs_data), font=("Arial", 22), bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR)
            main_button.pack(fill=tk.BOTH)

            button_frame = tk.Frame(item_frame, bg=BACKGROUND_COLOR)
            button_frame.pack(fill=tk.X)

            minus_button = tk.Button(button_frame, text="-", width=5, command=lambda x=i, c=counts, cl=count_labels, a=amounts: update_count(x, -1, c, cl, total_count_label, total_amount_label, a, tabs_data), font=("Arial", 17), bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR)
            minus_button.pack(side=tk.LEFT, expand=True, fill=tk.X)

            plus_button = tk.Button(button_frame, text="+", width=5, command=lambda x=i, c=counts, cl=count_labels, a=amounts: update_count(x, 1, c, cl, total_count_label, total_amount_label, a, tabs_data), font=("Arial", 17), bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR)
            plus_button.pack(side=tk.RIGHT, expand=True, fill=tk.X)

            label = tk.Label(item_frame, text="0個", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Arial", 17))
            label.pack()
            count_labels.append(label)

        # 各タブごとに必要な変数を保存
        data['counts'] = counts
        data['count_labels'] = count_labels

    # def run_add_money_program():
    #     subprocess.run(["python", "add_money.py"])

    #水交換時刻、掃除時刻、現在時刻を表示
    def save_task_time(label, filename='task_times.json'):
        if hasattr(label, 'last_update'):
            task_time = label.last_update.strftime('%Y-%m-%d %H:%M:%S')
            task_name = label.cget('text').split()[0]  # "水交換" または "掃除"
            try:
                with open(filename, 'r') as f:
                    task_times = json.load(f)
            except FileNotFoundError:
                task_times = {}
            task_times[task_name] = task_time
            with open(filename, 'w') as f:
                json.dump(task_times, f)
    def load_task_times(filename='task_times.json'):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    def save_task_time(label, filename='task_times.json'):
        if hasattr(label, 'last_update'):
            task_time = label.last_update.strftime('%Y-%m-%d %H:%M:%S')
            task_name = 'water_change' if label == water_change_label else 'cleaning'
            try:
                with open(filename, 'r') as f:
                    task_times = json.load(f)
            except FileNotFoundError:
                task_times = {}
            task_times[task_name] = task_time
            with open(filename, 'w') as f:
                json.dump(task_times, f)
    def load_task_times(filename='task_times.json'):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    def update_time():
        current_time = datetime.now()
        time_label.config(text=f"現在 {current_time.strftime('%m/%d %H:%M')}")
        check_task_times(current_time)
        time_label.after(1000, update_time)
    def update_task_time(task_label):
        current_time = datetime.now()
        task_label.config(text=f"{current_time.strftime('%m/%d %H:%M')}")
        task_label.last_update = current_time
        save_task_time(task_label)
        check_task_times(current_time)

    #規定時間経過後に文字の色を変える
    def check_task_times(current_time):
        for label in [water_change_label, cleaning_label]:
            if hasattr(label, 'last_update'):
                time_diff = current_time - label.last_update
                if time_diff > timedelta(hours= 12):
                    label.config(fg='yellow')
                else:
                    label.config(fg=TEXT_COLOR)

    def initialize_labels():
        task_times = load_task_times()
        for label, task_name in [(water_change_label, 'water_change'), (cleaning_label, 'cleaning')]:
            if task_name in task_times:
                last_update = datetime.strptime(task_times[task_name], '%Y-%m-%d %H:%M:%S')
                label.config(text=f"{last_update.strftime('%m/%d %H:%M')}")
                label.last_update = last_update
            else:
                label.config(text="記録なし")

    top_frame = tk.Frame(win, bg=BACKGROUND_COLOR)
    top_frame.pack(side=tk.TOP, fill=tk.X)

    # 現在時刻
    time_label = tk.Label(top_frame, font=('Arial', 20), bg=BACKGROUND_COLOR, fg=TEXT_COLOR)
    time_label.pack(side=tk.RIGHT)

    # 掃除のラベルとボタン
    cleaning_label = tk.Label(top_frame, text="記録なし", font=('Arial', 20), bg=BACKGROUND_COLOR, fg=TEXT_COLOR)
    cleaning_label.pack(side=tk.RIGHT, padx=(1, 50))

    cleaning_button = tk.Button(top_frame, text="掃除", command=lambda: update_task_time(cleaning_label), 
                                font=("Arial", 18), bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR)
    cleaning_button.pack(side=tk.RIGHT)

    # 水交換のラベルとボタン
    water_change_label = tk.Label(top_frame, text="記録なし", font=('Arial', 20), bg=BACKGROUND_COLOR, fg=TEXT_COLOR)
    water_change_label.pack(side=tk.RIGHT, padx=(1, 50))

    water_change_button = tk.Button(top_frame, text="水交換", command=lambda: update_task_time(water_change_label), 
                                    font=("Arial",18), bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR)
    water_change_button.pack(side=tk.RIGHT)


    #メイン画面にボタンを表示するフレームを作成
    bottom_frame = tk.Frame(win, bg=BACKGROUND_COLOR)
    bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=0)

    left_frame = tk.Frame(bottom_frame, bg=BACKGROUND_COLOR)
    left_frame.pack(side=tk.LEFT, padx=20)

    reset_button = tk.Button(left_frame, text="リセット", command=lambda: reset_counts(tabs_data, total_count_label, total_amount_label), font=("Arial", 25), width=9,bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR)
    reset_button.pack(side=tk.LEFT, padx=10)

    history_button = tk.Button(left_frame, text="履歴確認", command=check_balance, font=("Arial", 25), width=9, bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR)
    history_button.pack(side=tk.LEFT, padx=10)

    add_money_button = tk.Button(left_frame, text="チャージ", command=add_money, font=("Arial", 25), width=9, bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR)
    add_money_button.pack(side=tk.LEFT, padx=10)

    management_button = tk.Button(left_frame, text="管理", command=management, font=("Arial", 25), width=6, bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR)
    management_button.pack(side=tk.LEFT, padx=10)

    right_frame = tk.Frame(bottom_frame, bg=BACKGROUND_COLOR)
    right_frame.pack(side=tk.RIGHT, padx=20)

    total_count_label = tk.Label(right_frame, text="合計個数: 0個", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Arial", 24))
    total_count_label.pack(side=tk.LEFT, padx=10)

    total_amount_label = tk.Label(right_frame, text="合計金額: 0円", bg=BACKGROUND_COLOR, fg=TEXT_COLOR, font=("Arial", 24))
    total_amount_label.pack(side=tk.LEFT, padx=10)

    confirm_button = tk.Button(right_frame, text="支払い", command=show_summary, font=("Arial", 25), width=10, bg=BUTTON_COLOR, fg=BUTTON_TEXT_COLOR)
    confirm_button.pack(side=tk.LEFT, padx=10)

    initialize_labels()
    update_time()
    #ウィンドウを動かす
    win.mainloop()

main()
