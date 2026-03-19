import sys
import numpy as np
import random as rn
import torch
from torch import nn
from transformers import AutoModel, AutoTokenizer

class FakeReviewClassifier(nn.Module):
    def __init__(self, dropout=0.1):
        super(FakeReviewClassifier, self).__init__()

        self.bert = AutoModel.from_pretrained("activebus/BERT_Review")

        self.dropout = nn.Dropout(dropout)
        self.linear = nn.Linear(768, 1)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, tokens, masks=None):
        bert_output = self.bert(tokens, attention_mask=masks)
        dropout_output = self.dropout(bert_output.pooler_output)
        linear_output = self.linear(dropout_output)
        proba = self.sigmoid(linear_output)
        return proba


class FakeReviewClassifier_rating(nn.Module):
    def __init__(self, dropout=0.1,batch_size=4):
        super(FakeReviewClassifier_rating, self).__init__()

        self.bert = AutoModel.from_pretrained("activebus/BERT_Review")

        self.dropout = nn.Dropout(dropout)
        self.linear = nn.Linear(769, 1)
        self.sigmoid = nn.Sigmoid()
        self.batch_size = batch_size
    
    def forward(self, tokens, rating, masks=None):
        bert_output = self.bert(tokens, attention_mask=masks)
        dropout_output = self.dropout(bert_output.pooler_output)
        dropout_output = torch.cat((dropout_output,rating.reshape(self.batch_size,1)),1)
        linear_output = self.linear(dropout_output)
        proba = self.sigmoid(linear_output)
        return proba
    