
docker rm minio1
mkdir miniodata
docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  --name minio1 \
  -v $(pwd)/miniodata:/data \
  -e "MINIO_ROOT_USER=minio" \
  -e "MINIO_ROOT_PASSWORD=minio123" \
  quay.io/minio/minio server /data --console-address ":9001"

ulimit -n 65535
# ./release_tester/acquire_packages.py --new-version 3.7.15-nightly --source nightlypublic --zip  --enterprise --package-dir package_cache

./release_tester/test.py --new-version 3.7.15-nightly --enterprise --zip --verbose --package-dir $(pwd)/package_cache/ --test-data-dir "$(pwd)/data_dir" --starter-mode CL 
