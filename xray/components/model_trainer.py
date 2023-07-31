from xray.exception import XrayException
from xray.logger import logging
from xray.cnn.model.full_model import XrayModel
from xray.entity.artifact_entity import ModelTrainerArtifact, BaseModelArtifact, DataIngestionArtifact
from xray.entity.config_entity import ModelTrainerConfig
from xray.cnn.model.full_model import XrayModel
import os, sys
from xray.utils.common import read_yaml_file
from xray.constants.training_pipeline import PARAMS_FILE_PATH
import tensorflow as tf
from xray.cnn.metrics.classification_metric import get_classification_score


class ModelTrainer:
    def __init__(self, model_trainer_config: ModelTrainerConfig, base_model_artifact: BaseModelArtifact, data_ingestion_artifact: DataIngestionArtifact):
        try:
            self.model_trainer_config = model_trainer_config
            self.base_model_artifact = base_model_artifact
            self.data_ingestion_artifact = data_ingestion_artifact
            self._params_schema = read_yaml_file(PARAMS_FILE_PATH)
        except Exception  as e:
            raise XrayException(e,sys)        
        
    def initiate_model_trainer(self,) -> None:
        try:
            xraymodel = XrayModel(base_model_path= self.base_model_artifact)
            self.model = xraymodel.create_model()
            logging.info('model is created')

            self.model.compile(optimizer=self._params_schema['OPTIMIZER'], loss= self._params_schema['LOSS'],metrics=self._params_schema['METRICS'])
            logging.info('model is compiled successfully')
            train_datagen = tf.keras.preprocessing.image.ImageDataGenerator(
            rescale=1.0 / 255,
            shear_range=0.2,
            zoom_range=0.2,
            horizontal_flip=True)

            logging.info('train datagen is created')

            test_datagen = tf.keras.preprocessing.image.ImageDataGenerator(rescale=1.0 / 255)
            logging.info('test datagen is created')

            train_data = train_datagen.flow_from_directory(
            self.data_ingestion_artifact.trained_file_path,
            target_size=self._params_schema['IMAGE_SIZE'],
            batch_size=self._params_schema['BATCH_SIZE'],
            class_mode='binary')
            logging.info('Train data is done, read from parasm schema')

            test_data = test_datagen.flow_from_directory(
            self.data_ingestion_artifact.trained_file_path,
            target_size=self._params_schema['IMAGE_SIZE'],
            batch_size=self._params_schema['BATCH_SIZE'],
            class_mode='binary')
            logging.info('Test data is done, read from parasm schema')

            self.model.fit(
                train_data,
                steps_per_epoch=len(train_data),
                epochs=self._params_schema['EPOCHS'],
                validation_data=test_data,
                validation_steps=len(test_data)
            )
            logging.info('Model is trained successfully')


            true_train_lable = train_data.classes
            logging.info(f"true_train_lable: {true_train_lable}")
            true_test_lable = test_data.classes
            logging.info(f"true_test_lable: {true_test_lable}")


            training_prediction =self.model.predict(train_data)
            logging.info(f"training_prediction: {training_prediction}")
            training_predicted_labels = (training_prediction > 0.5).astype(int)
            logging.info(f"training_predicted_labels: {training_predicted_labels}")
            train_accuracy_score = get_classification_score(true_train_lable,training_predicted_labels).model_accuracy
            logging.info(f"training_accuracy_score: {train_accuracy_score}")

            if train_accuracy_score < self.model_trainer_config.expected_accuracy:
                raise Exception('Training Accuracy is less than expected accuracy')
            
            test_prediction = self.model.predict(test_data)
            test_predicted_labels = (test_prediction > 0.5).astype(int)
            test_accuracy_score = get_classification_score(true_test_lable,test_predicted_labels).model_accuracy
            logging.info(f"test_accuracy_score: {test_accuracy_score}")

            diff = abs(train_accuracy_score - test_accuracy_score)
            logging.info(f"diff: {diff}")
            if diff > self.model_trainer_config.overfit_threshold:
                raise Exception('Model is overfit accuracy')

            os.makedirs(os.path.dirname(self.model_trainer_config.trained_model_file_path), exist_ok=True)
            self.model.save(self.model_trainer_config.trained_model_file_path, overwrite= True)
            logging.info('Model is saved successfully')

            model_trainer_artifact = ModelTrainerArtifact(trained_model_file_path=self.model_trainer_config.trained_model_file_path)
            logging.info('ModelTrainerArtifact is created successfully')
            logging.info(f'ModelTrainerArtifact: {model_trainer_artifact}')
            return model_trainer_artifact

        except Exception as e:
            raise XrayException(e,sys)

