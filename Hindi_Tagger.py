import stanza
from pdfminer.high_level import extract_text
import csv
import os

def setup_stanza(lang_code='hi'):
    stanza.download(lang_code)
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
                word.id,
                word.text,
                word.lemma,
                word.upos,
                word.xpos
            ])
    return tagged_data

def save_to_csv(tagged_data, output_csv_path):
    headers = ["ID", "Word", "Lemma", "UPOS", "XPOS"]
    with open(output_csv_path, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(tagged_data)
    print(f"✅ POS-tagged output saved to: {output_csv_path}")

def main(pdf_path, output_csv_path, lang_code='hi'):
    print("🔄 Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)

    if not text:
        print("❌ No text extracted.")
        return

    print("🧠 Setting up NLP pipeline...")
    nlp = setup_stanza(lang_code)

    print("📝 Performing POS tagging...")
    tagged_data = pos_tag_text(nlp, text)

    print("💾 Saving results...")
    save_to_csv(tagged_data, output_csv_path)

if __name__ == "__main__":
    input_pdf = "sample_hindi.pdf"  # Replace with your PDF file path
    output_csv = "hindi_pos_output.csv"
    main(input_pdf, output_csv)
