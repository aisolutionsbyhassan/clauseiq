from docx import Document

doc = Document()
with open('c:/Users/Administrator/Desktop/high_risk_test_contract.txt', 'r', encoding='utf-8') as f:
    doc.add_paragraph(f.read())
doc.save('c:/Users/Administrator/Desktop/clauseiq/high_risk_test_contract.docx')
print("Done")
