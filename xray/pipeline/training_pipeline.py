from xray.exception import XrayException
from xray.logger import logging
from xray.entity.config_entity import TrainingPipelineConfig,DataIngestionConfig,DataValidationConfig,BaseModelConfig, ModelTrainerConfig
from xray.entity.artifact_entity import DataIngestionArtifact,DataValidationArtifact, BaseModelArtifact, ModelTrainerArtifact
import os, sys
from xray.components.data_ingestion import DataIngestion
from xray.components.data_validation import DataValidation
from xray.components.model_trainer import ModelTrainer
from xray.cnn.model.base_model import BaseModel

class  Trainipipeline:
    def __init__(self,):
        self.training_pipeline_config = TrainingPipelineConfig()
    
    def start_data_ingestion(self)-> DataIngestionArtifact:
        try:
            self.data_ingestion_config = DataIngestionConfig(training_pipeline_config=self.training_pipeline_config)
            logging.info("Starting data ingestion")
            data_ingestion = DataIngestion(data_ingestion_config=self.data_ingestion_config)
            data_ingestion_artifact = data_ingestion.initiate_data_ingestion()
            return data_ingestion_artifact
        except XrayException as e:
            raise XrayException(e,sys)
        
    def start_data_validation(self, data_ingestion_artifact: DataIngestionArtifact)->DataValidationArtifact:
         try:
            logging.info("Starting data validation")
            self.data_validation_config = DataValidationConfig(training_pipeline_config=self.training_pipeline_config)
            data_validation = DataValidation(data_validation_config=self.data_validation_config,data_ingestion_artifact= data_ingestion_artifact )
            data_validation_artifact = data_validation.initiate_data_validation()

         except XrayException as e:
                     raise XrayException(e,sys)
         
    def base_model(self,):
        base_model_config = BaseModelConfig()
        base_model = BaseModel(base_model_config)
        base_model_artifact = base_model.get_base_model()
        return base_model_artifact
    
    def start_model_training(self, data_ingestion_artifact:DataIngestionArtifact, base_model_artifact:BaseModelArtifact):
         try:
            logging.info('starting the model training')
            self.model_training_config = ModelTrainerConfig(training_pipeline_config= self.training_pipeline_config)
            model_trainer = ModelTrainer(model_trainer_config=self.model_training_config, base_model_artifact=base_model_artifact, data_ingestion_artifact=data_ingestion_artifact)
            model_trainer_artifact = model_trainer.initiate_model_trainer()
            return model_trainer_artifact
         except Exception as e:
            raise XrayException(e,sys)
         
    

         
    def run_pieline(self):
        try:
            data_ingestion_artifact = self.start_data_ingestion()
            data_validation_artifact = self.start_data_validation(data_ingestion_artifact)
            base_model_artifact = self.base_model()
            model_trainer_artifact = self.start_model_training(data_ingestion_artifact, base_model_artifact)
        except XrayException as e:
                raise XrayException(e,sys)