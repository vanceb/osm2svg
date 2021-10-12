from app import app, q
from flask import jsonify, request, abort, render_template, Response
import xml.etree.ElementTree as ET

from redis import Redis
from rq.job import Job, JobStatus
from rq.exceptions import NoSuchJobError

import job


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template("index.html")
    else:
        job_def = request.json
        if job_def is None:
            result = {"Error": "Unable to parse json job request"}
            return jsonify(result), 400

        result = q.enqueue(job.run_job, app.config["MAP_CONFIG"], job_def)
        return result.id


@app.route('/<id>', methods=['GET'])
def get_result(id):
    try:
        mapjob = Job.fetch(id, connection=Redis())
    except NoSuchJobError:
        return abort(404) 

    if mapjob.is_finished:
        return ET.tostring(mapjob.result), 200, {'Content-Type': 'image/svg+xml'}

    elif mapjob.is_queued:
        result = {"Status": "Queued"}
    elif mapjob.is_started:
        result = {"Status": "Started"}
    elif mapjob.is_failed:
        result = {"Status": "Failed - Maybe timed out, please select a smaller area or fewer features"}
    elif mapjob.is_deferred:
        result = {"Status": "Job deferred"}

    return jsonify(result)


    
