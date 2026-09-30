from diagrams import Diagram, Edge
from diagrams.aws.storage import S3
from diagrams.aws.compute import Lambda
from diagrams.aws.ml import Comprehend, Polly
from diagrams.aws.integration import SNS

with Diagram("architecture", show=False, direction="LR", filename="docs/architecture"):
    input_bucket = S3("Input Bucket")
    tts_lambda = Lambda("TTS Handler")
    comprehend = Comprehend("Comprehend")
    polly = Polly("Polly")
    output_bucket = S3("Output Bucket")
    sns = SNS("SNS Topic")
    notifier_lambda = Lambda("Notifier")

    input_bucket >> Edge(label="triggers") >> tts_lambda
    tts_lambda >> Edge(label="detect language") >> comprehend
    tts_lambda >> Edge(label="synthesize speech") >> polly
    tts_lambda >> Edge(label="store .mp3") >> output_bucket
    output_bucket >> Edge(label="triggers") >> notifier_lambda
    notifier_lambda >> Edge(label="publish") >> sns