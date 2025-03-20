"""
Factory for document processing components.
"""

from typing import Dict, List, Optional, Any, Type
import logging
from z888_ai_hub.storage.database.client import SupabaseStorage
from z888_ai_hub.processors.document_processor import DocumentProcessor
from z888_ai_hub.connectors.factory import ConnectorFactory
from z888_ai_hub.connectors.base_connector import ConnectorCapability, ConnectorConfig, BaseConnector
from z888_ai_hub.utils.file_collector import FileCollector
from z888_ai_hub.processors.pdf_processor import PdfProcessor
from z888_ai_hub.processors.doc_processor import DocProcessor

logger = logging.getLogger(__name__)

class DocumentProcessorFactory:
    """Factory for creating document processors."""
    
    _file_collector_class: Type[FileCollector] = FileCollector
    _storage_class: Type[SupabaseStorage] = SupabaseStorage
    
    @classmethod
    def set_file_collector_class(cls, collector_class: Type[FileCollector]) -> None:
        """
        Set file collector class for testing purposes.
        
        Args:
            collector_class: FileCollector class or mock
        """
        cls._file_collector_class = collector_class
    
    @classmethod
    def set_storage_class(cls, storage_class: Type[SupabaseStorage]) -> None:
        """
        Set storage class for testing purposes.
        
        Args:
            storage_class: SupabaseStorage class or mock
        """
        cls._storage_class = storage_class
    
    @staticmethod
    def _validate_connector_config(connector_config: Dict[str, ConnectorConfig]) -> None:
        """
        Validate connector configuration.
        
        Args:
            connector_config: Configuration to validate
            
        Raises:
            ValueError: If configuration is invalid
        """
        if not connector_config:
            raise ValueError("Connector configuration is empty")
            
        if "connectors" not in connector_config:
            raise ValueError("Missing 'connectors' key in configuration")
            
        connectors = connector_config["connectors"]
        if not isinstance(connectors, dict):
            raise ValueError("'connectors' must be a dictionary")
            
        for connector_name, config in connectors.items():
            if not isinstance(config, dict):
                raise ValueError(f"Invalid configuration for connector {connector_name}: must be a dictionary")
                
            if "type" not in config:
                raise ValueError(f"Missing 'type' field in configuration for connector {connector_name}")
                
            if "enabled" in config and not config["enabled"]:
                logger.warning(f"Connector {connector_name} is disabled in configuration")
                
            if "capabilities" in config:
                capabilities = config["capabilities"]
                if not isinstance(capabilities, list):
                    raise ValueError(f"Invalid capabilities for connector {connector_name}: must be a list")
                    
                for capability in capabilities:
                    if not isinstance(capability, str):
                        raise ValueError(f"Invalid capability for connector {connector_name}: must be a string")
                    try:
                        ConnectorCapability[capability.upper()]
                    except KeyError:
                        raise ValueError(f"Unknown capability '{capability}' for connector {connector_name}")
    
    @staticmethod
    def _validate_connector_capabilities(connector: BaseConnector, required_capability: ConnectorCapability) -> None:
        """
        Validate connector capabilities.
        
        Args:
            connector: Connector to validate
            required_capability: Required capability
            
        Raises:
            ValueError: If connector doesn't have required capability
        """
        if required_capability not in connector.capabilities:
            raise ValueError(f"Connector must have {required_capability} capability")
    
    @classmethod
    async def create_processor(
        cls,
        root_path: str,
        connector_config: Dict[str, ConnectorConfig],
        required_capabilities: Optional[List[ConnectorCapability]] = None
    ) -> DocumentProcessor:
        """
        Create document processor with specified capabilities.
        
        Args:
            root_path: Root path for file collection
            connector_config: Configuration for connectors
            required_capabilities: List of required connector capabilities.
                                If None, will use default capabilities.
            
        Returns:
            DocumentProcessor: Configured document processor
            
        Raises:
            ValueError: If required connectors are not found or configuration is invalid
        """
        # Валидация конфигурации
        try:
            cls._validate_connector_config(connector_config)
        except ValueError as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            raise
            
        if required_capabilities is None:
            required_capabilities = [
                ConnectorCapability.SUMMARY,
                ConnectorCapability.VECTORIZATION
            ]
        
        logger.info(f"Creating document processor with capabilities: {required_capabilities}")
        logger.debug(f"Available connector types: {list(connector_config['connectors'].keys())}")
        
        # Создаем коннекторы с нужными возможностями
        connectors = {}
        initialization_errors = {}
        
        try:
            connectors = await ConnectorFactory.create_connectors_for_tasks(
                connector_config,
                required_capabilities
            )
        except Exception as e:
            logger.error(f"Failed to create connectors: {str(e)}")
            initialization_errors["general"] = str(e)
        
        logger.info(f"Created {len(connectors)} connectors")
        
        # Находим коннекторы с нужными возможностями
        summary_generator = None
        vectorizer = None
        
        for connector_name, connector in connectors.items():
            logger.debug(f"Checking connector {connector_name} with capabilities: {connector.capabilities}")
            
            if ConnectorCapability.SUMMARY in connector.capabilities:
                summary_generator = connector
                logger.info(f"Found summary generator: {connector_name}")
            if ConnectorCapability.VECTORIZATION in connector.capabilities:
                vectorizer = connector
                logger.info(f"Found vectorizer: {connector_name}")
        
        if not summary_generator or not vectorizer:
            missing_capabilities = []
            if not summary_generator:
                missing_capabilities.append(ConnectorCapability.SUMMARY)
            if not vectorizer:
                missing_capabilities.append(ConnectorCapability.VECTORIZATION)
                
            error_msg = (
                f"Required connectors not found.\n"
                f"Missing capabilities: {missing_capabilities}\n"
                f"Available connector types: {list(connector_config['connectors'].keys())}\n"
                f"Successfully created connectors: {list(connectors.keys())}\n"
            )
            
            if initialization_errors:
                error_msg += f"Initialization errors: {initialization_errors}\n"
                
            # Проверяем, есть ли коннекторы в конфиге с нужными возможностями
            for connector_name, config in connector_config["connectors"].items():
                if "type" in config:
                    connector_type = config["type"]
                    if connector_type not in connectors:
                        error_msg += f"Connector {connector_name} ({connector_type}) failed to initialize\n"
            
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Проверяем возможности коннекторов
        try:
            cls._validate_connector_capabilities(summary_generator, ConnectorCapability.SUMMARY)
            cls._validate_connector_capabilities(vectorizer, ConnectorCapability.VECTORIZATION)
        except ValueError as e:
            logger.error(f"Connector capabilities validation failed: {str(e)}")
            raise
        
        # Создаем процессоры файлов
        pdf_processor = PdfProcessor()
        doc_processor = DocProcessor()
        
        logger.info("Creating document processor with all components")
        
        return DocumentProcessor(
            storage=cls._storage_class(),
            summary_generator=summary_generator,
            vectorizer=vectorizer,
            file_collector=cls._file_collector_class(root_path),
            pdf_processor=pdf_processor,
            doc_processor=doc_processor
        )
    
    @classmethod
    async def create_default(cls, root_path: str, connector_config: Dict[str, ConnectorConfig]) -> DocumentProcessor:
        """
        Create default document processor with standard components.
        
        Args:
            root_path: Root path for file collection
            connector_config: Configuration for connectors
            
        Returns:
            DocumentProcessor: Configured document processor
        """
        return await cls.create_processor(
            root_path=root_path,
            connector_config=connector_config,
            required_capabilities=[
                ConnectorCapability.SUMMARY,
                ConnectorCapability.VECTORIZATION
            ]
        ) 