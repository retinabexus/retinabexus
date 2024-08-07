import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import torch
import pickle
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.nn.init as init
import torch.optim as optim


# data una sequenza temporale restituisce i il quaternioni al tempo successivo
def AI(x,model,scaler):
  model.eval()
  x = scaler.transform(x)
  x = torch.tensor(x, dtype=torch.float32)
  x = x.unsqueeze(0)
  y = model(x)
  y = y.detach().numpy()
  return y



class GRUsinglelayer(nn.Module):
    def __init__(self, input_size, hidden_size, output_size, num_layers, dp=0.3):
        super(GRUsinglelayer, self).__init__()

        self.num_layers = num_layers
        self.hidden_dim = hidden_size
        self.gru = nn.GRU(input_size=input_size, hidden_size=hidden_size, dropout=dp, bidirectional=False, batch_first=True, num_layers=num_layers)

        # self.linear1 = nn.Linear(self.hidden_dim  , self.hidden_dim ) # bisogna moltiplicare per 2 perchè la rete bidirezionale raddoppia l'output
        self.linear2 = nn.Linear(self.hidden_dim  , output_size  )
        # self.relu = nn.ReLU()
    def forward(self, x):
        batch_size = x.shape[0]
        # valore iniziale per hidden state e cell state (inzializziamo a zero)
        # NOTA: internamente per h e c pytorch usa la shape (numero di layers, batch size, hidden units)
        h0 = torch.zeros(self.num_layers, batch_size, self.hidden_dim , device=x.device).requires_grad_()
        #h0=h0.double()
        pred, hidden  = self.gru(x,h0)




        out = self.linear2(hidden[0])
        # out = self.relu(out)
        # out = self.linear2(out)


        #out, _ = self.gru(x, h0)
        #out = self.linear2(out[:, -1, :])
        out = F.normalize(out, p=2, dim=1)
        return out