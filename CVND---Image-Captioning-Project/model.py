import torch
import torch.nn as nn
import torchvision.models as models


class EncoderCNN(nn.Module):
    def __init__(self, embed_size):
        super(EncoderCNN, self).__init__()
        resnet = models.resnet50(pretrained=True)
        for param in resnet.parameters():
            param.requires_grad_(False)
        
        modules = list(resnet.children())[:-1]
        self.resnet = nn.Sequential(*modules)
        self.embed = nn.Linear(resnet.fc.in_features, embed_size)

    def forward(self, images):
        features = self.resnet(images)
        features = features.view(features.size(0), -1)
        features = self.embed(features)
        return features
    

class DecoderRNN(nn.Module):
    def __init__(self, embed_size, hidden_size, vocab_size, num_layers=1):
        super(DecoderRNN, self).__init__()
        self.embed_size = embed_size
        self.hidden_size = hidden_size
        self.vocab_size = vocab_size
        self.num_layers = num_layers
        
        self.word_embeddings = nn.Embedding(vocab_size, embed_size)
        self.lstm = nn.LSTM(embed_size, hidden_size, num_layers, batch_first = True)
        self.hidden2out=nn.Linear(hidden_size,vocab_size)
        self.softmax = nn.LogSoftmax(dim=1)
        
        
    
    def forward(self, features, captions):
        captions = self.word_embeddings(captions[:,:-1])
        embed = torch.cat((features.unsqueeze(1), captions), dim=1)
        lstm_out, _ = self.lstm(embed)
        outputs = self.hidden2out(lstm_out)
        return outputs

    def sample(self, inputs, states=None, max_len=20):
        " accepts pre-processed image tensor (inputs) and returns predicted sentence (list of tensor ids of length max_len) "
        out = []
        for i in range(max_len): #until we sample til max length
            lstm_out, states = self.lstm(inputs, states) #(1,1,hidden_state)
            outputs = self.hidden2out(lstm_out.squeeze(1)) #(1,vocab_size)
            _, predicted = outputs.max(dim=1) #(1,1)
            out.append(predicted.item()) #store predicted word
            inputs = self.word_embeddings(predicted) #(1,embeded_size)
            inputs = inputs.unsqueeze(1) # (1,1,hidden_state)
        return out