import sys
import numpy as np
import random as rn
import torch
from torch import nn

from torch.utils.data import TensorDataset, DataLoader, RandomSampler, SequentialSampler
from torch.optim import Adam
from torch.nn.utils import clip_grad_norm_
from IPython.display import clear_output
from Model import FakeReviewClassifier
from sklearn.metrics import classification_report
from transformers import AutoModel, AutoTokenizer
import pickle

import os
import pandas
import random
from sklearn.model_selection import train_test_split
import split_sentence

def load_dataset_zip(path, shuffle=True,shuffle_size=20000):
    '''
        Load yelpzip dataset
        Path: location of the dataset, should contains metadata and reviewcontentd
        Return: Merged dataset
    '''
    meta_data_path = path + 'metadata'
    review_content_path = path + 'reviewContent'

    assert os.path.exists(meta_data_path)
    assert os.path.exists(review_content_path)

    meta_data = pandas.read_csv(meta_data_path,sep='\t')
    review_content = pandas.read_csv(review_content_path,sep='\t')
    data = meta_data.merge(review_content,how='inner',suffixes=('','_y'))
    data.drop(data.filter(regex='_y$').columns, axis=1, inplace=True)

    print(f'In the dataset there are {len(data[data.label==-1])} fake reviews and {len(data[data.label==1])} real reviews')

    # data = pandas.concat([data[data.label==-1][:20000],data[data.label==1][-20000:]])

    if shuffle:
        fake_reviews = data[data.label==-1]
        fake_reviews.label = 0

        real_reviews = data[data.label==1]

        fake_reviews = fake_reviews.reset_index()
        real_reviews = real_reviews.reset_index()
        
        fake_index = random.sample(range(fake_reviews.index.min(),fake_reviews.index.max() + 1),shuffle_size)
        real_index = random.sample(range(real_reviews.index.min(),fake_reviews.index.max() + 1),shuffle_size)

        data = pandas.concat([fake_reviews.iloc[fake_index],real_reviews.iloc[real_index]])
        data = data.reset_index()

    print(f"Loaded {len(data)} rows")
    print(f'Using {len(data[data.label==-1])} fake reviews and {len(data[data.label==1])} real reviews')

    return data

# output_data_path = 'data/splited_data.bin'
# path_model = "/root/model.pkl"
# path_state_dict = "/root/model_state_dict.pkl"

output_data_path = 'splited_data.bin'
path_model = "model.pkl"
path_state_dict = "model_state_dict.pkl"


BATCH_SIZE = 4
EPOCHS = 10

tokenizer = AutoTokenizer.from_pretrained("activebus/BERT_Review")


######### USE THIS FOR FIRST TRAINING #########
data = load_dataset_zip("PATH_TO_YOUR_DATA")
X_train, X_test, y_train, y_test = train_test_split(data.content, data.label, train_size=0.8, random_state=42)

with open(output_data_path,'wb') as file:
    pickle.dump((X_train, X_test, y_train, y_test), file)

######### USE THIS FOR FIRST TRAINING #########

X_train, X_test, y_train, y_test = pickle.load(open(output_data_path,'rb'))

train_tokens = list(map(lambda t: ['[CLS]'] + tokenizer.tokenize(split_sentence.add_sep(t),max_length=510,truncation=True) + ['[SEP]'], X_train))
test_tokens = list(map(lambda t: ['[CLS]'] + tokenizer.tokenize(split_sentence.add_sep(t),max_length=510,truncation=True) + ['[SEP]'], X_test))

print(len(train_tokens))
print(len(test_tokens))

print('padding..')

train_ids = [torch.tensor(tokenizer.convert_tokens_to_ids(tokens)) for tokens in train_tokens]
train_tokens_ids = torch.nn.utils.rnn.pad_sequence(train_ids,batch_first=True)

test_ids = [torch.tensor(tokenizer.convert_tokens_to_ids(tokens)) for tokens in test_tokens]
test_tokens_ids = torch.nn.utils.rnn.pad_sequence(test_ids,batch_first=True)


print('masking..')
train_masks = [[float(i > 0) for i in ii] for ii in train_tokens_ids]
test_masks = [[float(i > 0) for i in ii] for ii in test_tokens_ids]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# bert_clf = torch.load(path_model)
bert_clf = FakeReviewClassifier()
bert_clf.to(device)
# print(bert_clf.device)

train_y_tensor = torch.tensor(y_train.tolist()).float()

test_y_tensor = torch.tensor(y_test.tolist()).float()

train_masks_tensor = torch.tensor(train_masks)
test_masks_tensor = torch.tensor(test_masks)

train_dataset = TensorDataset(train_tokens_ids, train_masks_tensor, train_y_tensor)
train_sampler = RandomSampler(train_dataset)
train_dataloader = DataLoader(train_dataset, sampler=train_sampler, batch_size=BATCH_SIZE)

test_dataset = TensorDataset(test_tokens_ids, test_masks_tensor, test_y_tensor)
test_sampler = SequentialSampler(test_dataset)
test_dataloader = DataLoader(test_dataset, sampler=test_sampler, batch_size=BATCH_SIZE)

param_optimizer = list(bert_clf.sigmoid.named_parameters()) 
optimizer_grouped_parameters = [{"params": [p for n, p in param_optimizer]}]

optimizer = Adam(bert_clf.parameters(), lr=3e-6)

torch.cuda.empty_cache()

for epoch_num in range(EPOCHS):
    bert_clf.train()
    train_loss = 0
    for step_num, batch_data in enumerate(train_dataloader):
        token_ids, masks, labels = tuple(t.to(device) for t in batch_data)
        print(str(torch.cuda.memory_allocated(device)/1000000 ) + 'M')
        logits = bert_clf(token_ids, masks)
        
        loss_func = nn.BCELoss() 

        batch_loss = loss_func(logits.reshape(4), labels)
        train_loss += batch_loss.item()
        
        
        bert_clf.zero_grad()
        batch_loss.backward()
        
        clip_grad_norm_(parameters=bert_clf.parameters(), max_norm=1.0)
        optimizer.step()
        
        print('Epoch: ', epoch_num + 1)
        print("\r" + "{0}/{1} loss: {2} ".format(step_num, len(X_train) / BATCH_SIZE, train_loss / (step_num + 1)))
        
        if step_num % 1000 == 0:
            torch.save(bert_clf,path_model)
            torch.save(bert_clf.state_dict(),path_state_dict)
            

    bert_clf.eval()
    bert_predicted = []
    all_logits = []
    with torch.no_grad():
        for step_num, batch_data in enumerate(test_dataloader):

            token_ids, masks, labels = tuple(t.to(device) for t in batch_data)

            logits = bert_clf(token_ids, masks)
            loss_func = nn.BCELoss()
            loss = loss_func(logits.reshape(4), labels)
            numpy_logits = logits.cpu().detach().numpy()
            
            bert_predicted += list(numpy_logits[:, 0] > 0.5)
            all_logits += list(numpy_logits[:, 0])
    report = classification_report(y_test, bert_predicted)
    print(report)
    with open('epoch','a') as file:
        file.write('Epoch:' + str(epoch_num + 1))
        file.write(report)
        file.write('')

