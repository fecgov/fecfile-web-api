#!/bin/bash


# Create the k8s file to deploy flyway job after the container 
# has finished being created.
cat <<EOF >> function.yml
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  annotations:
    prometheus.io/scrape: "true"
  name: fecfile-func
spec:
  schedule: "*/1 * * * *"
  concurrencyPolicy: Allow
  successfulJobsHistoryLimit: 1
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: fecfile-func
            image:  813218302951.dkr.ecr.us-east-1.amazonaws.com/fecnxg-functions:$1
            args:
            - /bin/bash
            - -ec
            - python /opt/func/upload_report.py
            - sleep 15
            - python /opt/func/get_fec_number.py
            env:
              - name: DATA_RECEIVER_URL
                value: $3-efile-api.efdev.fec.gov/receiver
              - name: NEXGEN_DJANGO_API_URL
                value: $3-fecfile-api.efdev.fec.gov
              - name: DB_HOST
                value: $2
              - name: DB_NAME
                value: fecfile
              - name: DB_USER
                valueFrom:
                  secretKeyRef:
                    key: dbuser
                    name: db-creds
              - name: DB_PASSWD
                valueFrom:
                  secretKeyRef:
                    key: password
                    name: db-creds
          restartPolicy: Never
EOF

# create the job
kubectl --context=arn:aws:eks:us-east-1:813218302951:cluster/fecfile4 --namespace=$3 create -f function.yml
