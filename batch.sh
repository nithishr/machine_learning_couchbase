echo "packaging the model"
shiv --site-packages pipeline/ -o pipeline.pyz --platform manylinux1_x86_64 --python-version 39 --only-binary=:all: scikit-learn pandas category_encoders
echo "copying the model into Docker container"
docker cp pipeline.pyz ml_db:/tmp/
