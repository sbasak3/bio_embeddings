from webserver.utilities.configuration import configuration
from celery import Celery as _celery

task_keeper = _celery(
    broker=configuration["web"]["celery_broker_url"], backend="rpc://"
)

task_keeper.conf.task_routes = {
    'webserver.tasks.seqvec_embeddings.get_seqvec_embeddings_sync': {'queue': 'seqvec'},
    'webserver.tasks.seqvec_annotations.get_seqvec_annotations_sync': {'queue': 'seqvec_annotations'},
    'webserver.tasks.protbert_embeddings.get_protbert_embeddings_sync': {'queue': 'protbert'},
    'webserver.tasks.protbert_annotations.get_protbert_annotations_sync': {'queue': 'protbert_annotations'},
    'webserver.tasks.pipeline.run_pipeline': {'queue': 'pipeline'},
}
