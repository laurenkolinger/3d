
# PROJECT_DIR = '../TCRMP2025_3D'
# cd ../Panama25_3D/
export PROJECT_DIR=../Panama25_3D_subsample/


# mkdir -p $PROJECT_DIR/{video_source, processing,output}

# cp analysis_params.yaml $PROJECT_DIR/

python3 -m venv $PROJECT_DIR/.venv
source $PROJECT_DIR/.venv/bin/activate
pip install -r requirements.txt

# python src/utility/reset_full.py $PROJECT_DIR

# python src/step0.py $PROJECT_DIR

# METASHAPE_PATH = /home/bizon/applications/metashape-pro_2_2_2_amd64/metashape-pro/metashape 

# PYTHONPATH=$PROJECT_DIR/.venv/lib/python3.9/site-packages /home/bizon/applications/metashape-pro_2_2_2_amd64/metashape-pro/metashape -r src/step1.py $PROJECT_DIR

PYTHONPATH=$PROJECT_DIR/.venv/lib/python3.9/site-packages /home/bizon/applications/metashape-pro_2_2_2_amd64/metashape-pro/metashape -r src/step2.py $PROJECT_DIR

PYTHONPATH=$PROJECT_DIR/.venv/lib/python3.9/site-packages /home/bizon/applications/metashape-pro_2_2_2_amd64/metashape-pro/metashape -r src/step3.py $PROJECT_DIR

python3 src/utility/migrate_csv_to_new_format.py $PROJECT_DIR/status_TCRMP2025_3D_2.csv
python3 src/utility/migrate_csv_to_new_format.py $PROJECT_DIR/status_Panama25_3D.csv