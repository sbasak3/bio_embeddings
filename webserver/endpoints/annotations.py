from flask import request, abort
from flask_restx import Resource

from webserver.endpoints import api
from webserver.endpoints.request_models import sequence_post_parameters_annotations
from webserver.endpoints.task_interface import get_features
from webserver.endpoints.utils import check_valid_sequence
from webserver.utilities.parsers import (
    Source, Evidence, annotations_to_protvista_converter, SecondaryStructure, Disorder
)

ns = api.namespace("annotations", description="Get annotations on the fly.")


@ns.route('')
class Annotations(Resource):
    @api.expect(sequence_post_parameters_annotations, validate=True)
    @api.response(200, "Embedding in npy format")
    @api.response(400, "Invalid input. See return message for details.")
    @api.response(505, "Server error")
    def post(self):
        params = request.json

        sequence = params.get('sequence')

        if not sequence or len(sequence) > 2000 or not check_valid_sequence(sequence):
            return abort(400, "Sequence is too long or contains invalid characters.")

        model_name = params.get('model', 'seqvec')

        annotations = get_features(model_name, sequence)
        annotations['sequence'] = sequence

        format = params.get('format', 'legacy')

        if format == "protvista-predictprotein":
            source = Source(
                url=request.url,
                id="sync",
                name=f"bio_embeddings using {model_name}"
            )

            evidence = Evidence(
                source=source,
            )

            protvista_features = dict()
            protvista_features['sequence'] = sequence

            protvista_features['features'] = list()
            protvista_features['features'].extend(
                annotations_to_protvista_converter(
                    features_string=annotations['predictedDSSP8'],
                    evidences=[evidence],
                    type=f"SECONDARY_STRUCTURE_8_STATES_({model_name})",
                    feature_enum=SecondaryStructure
                )
            )
            protvista_features['features'].extend(
                annotations_to_protvista_converter(
                    features_string=annotations['predictedDSSP3'],
                    evidences=[evidence],
                    type=f"SECONDARY_STRUCTURE_3_STATES_({model_name})",
                    feature_enum=SecondaryStructure
                )
            )
            protvista_features['features'].extend(
                annotations_to_protvista_converter(
                    features_string=annotations['predictedDisorder'],
                    evidences=[evidence],
                    type=f"DISORDER_({model_name})",
                    feature_enum=Disorder
                )
            )

            return protvista_features
        elif format == "legacy":
            predictedCCO = {}
            predictedBPO = {}
            predictedMFO = {}

            for prediction in annotations['predictedCCO']:
                predictedCCO[prediction['GO_Term']] = max(predictedCCO.get(prediction['GO_Term'], -1), prediction['RI'])

            for prediction in annotations['predictedBPO']:
                predictedBPO[prediction['GO_Term']] = max(predictedBPO.get(prediction['GO_Term'], -1), prediction['RI'])

            for prediction in annotations['predictedMFO']:
                predictedMFO[prediction['GO_Term']] = max(predictedMFO.get(prediction['GO_Term'], -1), prediction['RI'])

            annotations['predictedCCO'] = predictedCCO
            annotations['predictedBPO'] = predictedBPO
            annotations['predictedMFO'] = predictedMFO

            return annotations

        elif format == "go-predictprotein":
            mapping_function = lambda x: {
                "gotermid": x['GO_Name'],
                "gotermname": x['GO_Term'],
                "gotermscore": int(x['RI']*100)
            }

            predictedCCO = {
                "ontology": "Cellular Component Ontology",
                "goTermWithScore": list(map(mapping_function, annotations['predictedCCO']))
            }
            predictedBPO = {
                "ontology": "Biological Process Ontology",
                "goTermWithScore": list(map(mapping_function, annotations['predictedBPO']))
            }
            predictedMFO = {
                "ontology": "Molecular Function Ontology",
                "goTermWithScore": list(map(mapping_function, annotations['predictedMFO']))
            }

            return [predictedBPO, predictedCCO, predictedMFO]

        else:
            abort(400, f"Wrong format passed: {format}")
