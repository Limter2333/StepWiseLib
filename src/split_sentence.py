def add_sep(doc):
    return doc.replace('.','. [SEP]').replace('?','? [SEP]').replace('!','! [SEP]')