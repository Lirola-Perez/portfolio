import numpy as np
import os
import matplotlib.pyplot as plt
from sklearn.linear_model import Ridge,Lasso,ElasticNet

class ModelTesting:
    def __init__(self,input_data,output_data) -> None:
        self.X = input_data
        self.Y = output_data

    def variable_separator(self,
        data,
        feature_names=None,
        file_name: str = "graphic"
    ):
        # Managing paths:
        out_dir = f"{os.getcwd()}/storage/graphs/"
        os.makedirs(out_dir, exist_ok=True)
        out_path = f"{out_dir}/{file_name}.png"
        print(out_path)

        #out_path = f"app/storage/{file_name}.png"
        arr = np.asarray(data)  # expected shape: (144, 12) -> (n_outputs, n_features)
        n_outputs, n_features = arr.shape
        print(f"DATA DIMENSIONS -> Outputs: {n_outputs}, Features: {n_features}")

        # Tall enough so all 144 output rows remain readable
        fig, ax = plt.subplots(figsize=(10, 10))
        # x is 144 times 12 features (144x12)
        x = [ i for _ in range(n_outputs) for i in range(n_features)] 
        y = arr.ravel()
        ax.scatter(x=x,y=y,marker=".")

        ax.set_title(f"{file_name} (Outputs and Input Features)", pad=12)
        ax.set_xlabel(f"Input Features for {file_name}")
        ax.set_ylabel(f"Output Index for {file_name}")

        ax.set_xticks(np.arange(n_features))
        if feature_names and len(feature_names) == n_features:
            ax.set_xticklabels(feature_names, rotation=40, ha="right", fontsize=9)
        else:
            ax.set_xticklabels([f"f{i}" for i in range(n_features)], fontsize=9)

        fig.tight_layout()
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        return out_path

    def plot_correlation_temp(self,
            data,
            feature_names=None,
            file_name: str = "graph_correlation"
        ):

        # Managing paths:
        out_dir = f"{os.getcwd()}/storage/graphs/"
        os.makedirs(out_dir, exist_ok=True)
        out_path = f"{out_dir}/{file_name}.png"

        arr = np.asarray(data)  # expected shape: (n_samples, n_features)
        n_features = arr.shape[1]

        # Compute (n_feat x n_feat) correlation across columns (rowvar=False treats columns as variables)
        corr = np.corrcoef(arr, rowvar=False)
        # Guard against NaNs if a constant column exists in a split
        corr = np.nan_to_num(corr, nan=0.0)

        fig, ax = plt.subplots(figsize=(9, 8))
        im = ax.imshow(corr, cmap="coolwarm", vmin=-1.0, vmax=1.0, aspect="auto")

        labels = (
            list(feature_names)
            if feature_names and len(feature_names) == n_features
            else [f"f{i}" for i in range(n_features)]
        )

        ax.set_xticks(np.arange(n_features))
        ax.set_yticks(np.arange(n_features))
        ax.set_xticklabels(labels, rotation=40, ha="right", fontsize=9)
        ax.set_yticklabels(labels, fontsize=9)

        ax.set_title("Input Feature Correlation Matrix (X_train_scaled)")
        cbar = fig.colorbar(im, ax=ax, shrink=0.85)
        cbar.set_label("Pearson Correlation")

        fig.tight_layout()
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        return out_path


    def regularizers(self,regularizer_type='Ridge', alpha=0.1):
        type = regularizer_type.lower()
        if type == 'ridge':
            reg = Ridge(alpha=alpha)
        elif type == 'lasso':
            reg = Lasso(alpha=alpha)
        elif type == 'elasticnet':
            reg = ElasticNet(alpha=alpha)
        else:
            raise ValueError

        reg.fit(self.X,self.Y)
        results = np.round(reg.coef_, 4)
        print(f"--- {regularizer_type} Coefficients ---")
        print(results)

        return results

