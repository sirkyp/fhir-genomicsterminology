from enum import Enum

class FHIRCodeSystem:
    def __init__(self):
        """
        Initialize a FHIR CodeSystem resource.
        """
        self.resourceType = "CodeSystem"

    def init(self, url, identifier=None, version=None, name=None, title=None, status="active", experimental=False, publisher=None, description=None, content="complete", contact=None, relatedArtifact=None, purpose=None):
        """
        Initialize a FHIR CodeSystem resource.

        :param url: Canonical URL of the CodeSystem (required).
        :param identifier: List of identifiers for the CodeSystem (optional).
        :param version: Version of the CodeSystem (optional).
        :param name: Name of the CodeSystem (optional).
        :param title: Title of the CodeSystem (optional).
        :param status: Status of the CodeSystem (default: "active").
        :param experimental: Whether the CodeSystem is experimental (default: False).
        :param publisher: Publisher of the CodeSystem (optional).
        :param description: Description of the CodeSystem (optional).
        :param relatedArtifact: Related artifacts for the CodeSystem (optional).
        :param content: Content mode of the CodeSystem (default: "complete").
        :param contact: Contact information for the CodeSystem (optional).
        :param purpose: Purpose of the CodeSystem (optional).
        """
        self.url = url
        self.identifier = identifier or []
        self.version = version
        self.name = name
        self.title = title
        self.status = status
        self.experimental = experimental
        self.publisher = publisher
        self.description = description
        self.relatedArtifact = relatedArtifact or []  # List of related artifacts for the CodeSystem
        self.content = content
        self.contact = contact or []  # List of contact information for the CodeSystem
        self.purpose = purpose  # Purpose of the CodeSystem
        self.property = []  # List of properties for the CodeSystem
        self.concept = []  # List of concepts in the CodeSystem

    def fetch_cs(self, url):
        """
        Fetch a CodeSystem from the given URL.

        :param url: URL of the CodeSystem to fetch.
        :return: FHIRCodeSystem instance or None if fetching fails.
        """
        import requests
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            data = response.json()
            self.init(data['url'],
                      identifier=data.get('identifier', []),
                      version=data.get('version'), 
                      name=data.get('name'),
                      title=data.get('title'), 
                      status=data.get('status', 'active'), 
                      experimental=data.get('experimental', False), 
                      publisher=data.get('publisher'), 
                      description=data.get('description'), 
                      contact=data.get('contact', []),
                      content=data.get('content', 'complete'))
            
        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching the CodeSystem: {e}")
            return None

    class PropertyType(str, Enum):
        CODE = "code"
        CODING = "Coding"
        STRING = "string"
        BOOLEAN = "boolean"
        INTEGER = "integer"
        DECIMAL = "decimal"
        DATETIME = "dateTime"

        def __str__(self):
            return self.value


    class Property:
        def __init__(self, code, type: 'FHIRCodeSystem.PropertyType', uri=None, description=None):
            """
            Initialize a FHIR CodeSystem Property.

            :param code: Code for the property (required).
            :param type: Type of the property (required).
            :param uri: URI for the property (optional).
            :param description: Description for the property (optional).
            :type type: PropertyType enum
            """
            if not isinstance(type, FHIRCodeSystem.PropertyType):
                raise ValueError("type must be a PropertyType enum")

            self.code = code
            self.uri = uri
            self.description = description
            self.type = type  # Store the string value of the enum

        def to_dict(self):
            """
            Convert the Property to a dictionary representation.
            """
            prop = {"code": self.code}
            prop["type"] = self.type
            if self.uri:
                prop["uri"] = self.uri
            if self.description:
                prop["description"] = self.description
            return prop
        
        def to_json(self):
            """
            Convert the Property to a JSON string representation.
            """
            import json
            return json.dumps(self.to_dict(), indent=2)

    def add_property(self, code, type: 'FHIRCodeSystem.PropertyType', uri=None, description=None):
        """
        Add a property to the CodeSystem.

        :param code: Code for the property (required).
        :param type: Type of the property (required).
        :param uri: URI for the property (optional).
        :param description: Description for the property (optional).
        :type type: PropertyType enum
        """
        if not isinstance(type, FHIRCodeSystem.PropertyType):
            raise ValueError("type must be a PropertyType enum")
        
        prop = FHIRCodeSystem.Property(code, type, uri, description)
        self.property.append(prop)

    def get_property(self, code):
        """
        Searches for a property in the CodeSystem by its code.

        :param code: Code of the property to search for.
        :return: The matching Property object or None if not found.
        """
        return next((prop for prop in self.property if prop.code == code), None)

    class Concept:
        def __init__(self, code, display=None, definition=None):
            """
            Initialize a FHIR CodeSystem Concept.

            :param code: Code for the concept (required).
            :param display: Display text for the concept (optional).
            :param definition: Definition of the concept (optional).
            
            """
            self.code = code
            self.display = display
            self.definition = definition
            self.properties = []

        def add_property(self, code, value, type : 'FHIRCodeSystem.PropertyType' = 'FHIRCodeSystem.PropertyType.STRING'):
            """
            Add a property to the Concept.

            :param code: Code for the property (required).
            :param value_string: String value for the property (required).
            """
            
            if not isinstance(type, FHIRCodeSystem.PropertyType):
                raise ValueError("type must be a PropertyType enum")

            prop = {"code": code}
            if type == FHIRCodeSystem.PropertyType.STRING:
                prop["valueString"] = value
            elif type == FHIRCodeSystem.PropertyType.CODE:
                prop["valueCode"] = value
            elif type == FHIRCodeSystem.PropertyType.CODING:
                prop["valueCoding"] = value
            elif type == FHIRCodeSystem.PropertyType.BOOLEAN:
                prop["valueBoolean"] = bool(value)
            elif type == FHIRCodeSystem.PropertyType.INTEGER:
                prop["valueInteger"] = int(value)
            elif type == FHIRCodeSystem.PropertyType.DECIMAL:
                prop["valueDecimal"] = float(value)
            elif type == FHIRCodeSystem.PropertyType.DATETIME:
                prop["valueDateTime"] = value

            self.properties.append(prop)

        def to_json(self):  
            """
            Convert the Concept to a JSON string representation.
            """
            import json
            return json.dumps(self.to_dict(), indent=2)

        def to_dict(self):
            """
            Convert the Concept to a dictionary representation.
            """
            concept = {
                "code": self.code
            }
            if self.display:
                concept["display"] = self.display
            if self.definition:
                concept["definition"] = self.definition
            if self.properties:
                concept["properties"] = self.properties
            return concept

    def add_concept(self, code, display=None, definition=None):
        """
        Add a concept to the CodeSystem.

        :param code: Code for the concept (required).
        :param display: Display text for the concept (optional).
        :param definition: Definition of the concept (optional).
        :param properties: Additional properties for the concept (optional).
        """
        concept = FHIRCodeSystem.Concept(code, display, definition)
        self.concept.append(concept)
        return concept

    def to_dict(self):
        """
        Convert the CodeSystem to a dictionary representation.

        :return: Dictionary representation of the CodeSystem.
        """
        return {
            "resourceType": self.resourceType,
            "url": self.url,
            "identifier": self.identifier,
            "version": self.version,
            "name": self.name,
            "title": self.title,
            "status": self.status,
            "experimental": self.experimental,
            "publisher": self.publisher,
            'contact': self.contact,
            "description": self.description,
            "purpose": self.purpose,
            "relatedArtifact": self.relatedArtifact,
            "content": self.content,
            "property": [property.to_dict() for property in self.property],
            "concept": [concept.to_dict() for concept in self.concept]
        }

    def to_json(self):
        """
        Convert the CodeSystem to a JSON string.

        :return: JSON string representation of the CodeSystem.
        """
        import json
        return json.dumps(self.to_dict(), indent=2)