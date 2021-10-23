from app import app, q
from flask import jsonify, request, abort, render_template, Response
import xml.etree.ElementTree as ET

from redis import Redis
from rq.job import Job, JobStatus
from rq.exceptions import NoSuchJobError


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

        result = q.enqueue("job.run_job", app.config["MAP_CONFIG"], job_def)
        app.logger.info(str(result.id) + " => " + str(job_def))
        return result.id

@app.route('/log', methods=['GET'])
def show_log():
    with open('/data/logs/map2laser.log', 'r') as f:
        l = f.read()
    return str(l), 200, {'Content-Type': 'text/plain'}

@app.route('/job/<id>', methods=['GET'])
def get_result(id):
    try:
        mapjob = Job.fetch(id, connection=Redis(host="redis", port="6379"))
    except NoSuchJobError:
        return abort(404) 

    if mapjob.is_finished:
        app.logger.info(str(id) + " =>  Completed")
        return ET.tostring(mapjob.result), 200, {'Content-Type': 'image/svg+xml'}

    elif mapjob.is_queued:
        result = {"Status": "Queued"}
    elif mapjob.is_started:
        result = {"Status": "Started"}
    elif mapjob.is_failed:
        app.logger.info(str(id) + " =>  Failed")
        result = {"Status": "Failed - Maybe timed out, please select a smaller area or fewer features"}
    elif mapjob.is_deferred:
        result = {"Status": "Job deferred"}

    return jsonify(result)


    
