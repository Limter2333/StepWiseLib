Follow the steps in the readme file in the [repo](https://github.com/kitman0000/BBCIM). 

# Train
If you have more than one GPU:
```
export PYTHONPATH=./

accelerate launch ./train.py
```
Otherwise, make sure you disable the multi_gpus in train.py, and directly run `python train.py`

# Inference
Follow the [repo](https://github.com/kitman0000/BBCIM) readme.

# Train on Your Own dataset
Replace the final classifer header to the number of your classes. And prepare the dataloader by yourself.

encoder_model.py
```python
class EmbeddingBasedIntentModel(torch.nn.Module):
    def __init__(self, embedding_model, device) -> None:
        super().__init__()
        self.n_classes = 18 # <---- Change this to your number
```

## Transfer Learning

Load the checkpoint and rewrite the forward function.
