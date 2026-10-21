from data_preparation import Input


data = Input()
X,Y = data.one_hot()
print(X,Y)