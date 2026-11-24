import zipfile, io, pandas as pd
pd.set_option('display.width',250); pd.set_option('display.max_columns',40); pd.set_option('display.max_rows',400); pd.set_option('display.max_colwidth',60)
z=zipfile.ZipFile('ext/epoch_zip/benchmark_data.zip')
for n in z.namelist(): print(n, z.getinfo(n).file_size)
rd=lambda n: pd.read_csv(io.BytesIO(z.read(n)))
fi=rd('epoch_capabilities_index/processed_data_for_eci.csv'); print(fi.shape); print(fi.head(5).T)
print(fi.groupby('benchmark').size().sort_values(ascending=False))
print(fi.Model.nunique(), fi.model_id.nunique() if 'model_id' in fi else '')
