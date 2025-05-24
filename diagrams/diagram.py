from diagrams import Diagram
from diagrams.aws.compute import EC2Instance
from diagrams.aws.general import Users 
from diagrams.aws.management import CloudwatchLogs
from diagrams.aws.iot import IotAnalyticsNotebook
from diagrams.aws.ml import SagemakerTrainingJob
from diagrams.oci.monitoring import HealthCheck
from diagrams.aws.compute import ElasticContainerServiceService
from diagrams.aws.management import SystemsManagerDocuments
from diagrams.alibabacloud.application import LogService 
from diagrams.aws.general import InternetAlt1
from diagrams.aws.database import Database
from diagrams.aws.management import TrustedAdvisorChecklist
from diagrams.aws.database import Timestream

with Diagram("Listener Worker", show=False, direction="TB"):
    l_worker =  EC2Instance("listener worker")
    forums = Users("forums")
    message = CloudwatchLogs("message")
    text = IotAnalyticsNotebook("text")
    filter = SagemakerTrainingJob("filter")
    a_storage = HealthCheck("add to file storage")
    file = SystemsManagerDocuments("file")
    z_txt = SystemsManagerDocuments("zip, rar, 7z, tar, text,...")
    z_tar = SystemsManagerDocuments("zip, rar, 7z, tar")
    t_file = SystemsManagerDocuments("text, csv, json, xml,...")
    extract = ElasticContainerServiceService("extract")
    type = LogService("type")
    type2 = LogService("type")
    download = InternetAlt1("download")
    s_storage = Database("save_to_storage")


    l_worker >> forums >> message 
    message >> text >> filter >> a_storage
    message  >> file >> type >> z_txt >> download >> type2 >> z_tar >> extract 

    type2 >> t_file >> s_storage
   
    extract >> type2

with Diagram("Reader Worker", show=False, direction="TB"):
    r_worker =  EC2Instance("reader worker")
    storage = Database("storage")
    file = SystemsManagerDocuments("file")
    filter = SagemakerTrainingJob("filter")
    m_data = TrustedAdvisorChecklist("matched data")
    a_dist = HealthCheck("add to file dist")

    r_worker >> storage >> file >> filter >> m_data >> a_dist

with Diagram("Web Backend Worker", show=False, direction="TB"):
    b_worker =  EC2Instance("backend worker")
    f_worker =  EC2Instance("frontend worker")
    dist = Database("dist")
    file = SystemsManagerDocuments("file")
    database = Timestream("database")
    

    b_worker >> dist >> file >> database
    b_worker >> f_worker

with Diagram("Web Frontend Worker", show=False, direction="TB"):
    f_worker =  EC2Instance("frontend worker")
    b_worker =  EC2Instance("backend worker")
    i_users = Users("interact with users")
    

    f_worker >> i_users
    f_worker >> b_worker
