import stanza
from pdfminer.high_level import extract_text
import csv
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Supported languages
LANG_OPTIONS = {
    "Hindi": "hi",
    "English": "en",
    "Marathi": "mr",
    "Tamil": "ta"
}

def setup_stanza(lang_code):
    stanza.download(lang_code, verbose=False)
    return stanza.Pipeline(lang_code)

def extract_text_from_pdf(pdf_path):
    try:
        text = extract_text(pdf_path)
        return text.strip()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def pos_tag_text(nlp, text):
    doc = nlp(text)
    tagged_data = []
    for sent in doc.sentences:
        for word in sent.words:
            tagged_data.append([
                word.id, word.text, word.lemma, word.upos, word.xpos
            ])
    return tagged_data

def save_to_csv(tagged_data, output_csv_path):
    headers = ["ID", "Word", "Lemma", "UPOS", "XPOS"]
    with open(output_csv_path, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(tagged_data)

def update_status(msg):
    status_label.config(text=msg)
    window.update_idletasks()

def main(pdf_path, output_csv_path, lang_code):
    update_status("🔄 Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)

    if not text:
        update_status("❌ No text extracted.")
        messagebox.showerror("Error", "No text extracted from the PDF.")
        return

    update_status("🧠 Setting up NLP pipeline...")
    nlp = setup_stanza(lang_code)

    update_status("📝 Performing POS tagging...")
    tagged_data = pos_tag_text(nlp, text)

    update_status("💾 Saving CSV output...")
    save_to_csv(tagged_data, output_csv_path)
    update_status("✅ Done! Output saved.")
    messagebox.showinfo("Success", f"POS-tagged CSV saved to:\n{output_csv_path}")

# ---------------- TKINTER UI ----------------

def select_pdf():
    pdf_path = filedialog.askopenfilename(
        title="Select PDF File",
        filetypes=[("PDF files", "*.pdf")]
    )
    if pdf_path:
        entry_pdf.delete(0, tk.END)
        entry_pdf.insert(0, pdf_path)

def run_pos_tagging():
    pdf_path = entry_pdf.get()
    if not pdf_path or not os.path.exists(pdf_path):
        messagebox.showerror("Error", "Please select a valid PDF file.")
        return

    lang_display = lang_dropdown.get()
    lang_code = LANG_OPTIONS.get(lang_display)
    if not lang_code:
        messagebox.showerror("Error", "Please select a language.")
        return

    output_csv_path = os.path.splitext(pdf_path)[0] + f"_{lang_code}_pos_output.csv"
    main(pdf_path, output_csv_path, lang_code)

# Setup Tkinter window
window = tk.Tk()
window.title("Multilingual PDF POS Tagger")
window.geometry("550x280")
window.resizable(False, False)

tk.Label(window, text="Select PDF File", font=("Arial", 12)).pack(pady=10)
frame = tk.Frame(window)
frame.pack()

entry_pdf = tk.Entry(frame, width=50)
entry_pdf.pack(side=tk.LEFT, padx=5)

btn_browse = tk.Button(frame, text="Browse", command=select_pdf)
btn_browse.pack(side=tk.LEFT, padx=5)

tk.Label(window, text="Select Language", font=("Arial", 12)).pack(pady=10)
lang_dropdown = ttk.Combobox(window, values=list(LANG_OPTIONS.keys()), state="readonly", width=20)
lang_dropdown.pack()
lang_dropdown.set("Hindi")  # Default selection

btn_run = tk.Button(window, text="Run POS Tagging", command=run_pos_tagging,
                    bg="#4CAF50", fg="white", font=("Arial", 12), pady=5)
btn_run.pack(pady=20)

status_label = tk.Label(window, text="", fg="gray", font=("Arial", 10))
status_label.pack(pady=5)

window.mainloop()
