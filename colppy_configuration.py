# DEFAULT VARIABLES

state = "testing"   # Change for production once tested
company_id = '19459'   # Ikitoi SA - Colppy Company ID
credentials = {
                "dev_user": {
                        "usuario": "guecaimburu.j@gmail.com",
                        "password": "43b4711b8e905725c891d62210e570ed"   # MD5
                         },
                "user": {
                        "usuario": "guecaimburu.j@gmail.com",
                        "password": "65b931fab44737bed4448e979d35d70d"   # MD5
                        }
                }

# DevPass: "LaCl@v3MasUltrasecret@DeTodasLasCl@v3s"

ccosts = {
            1: {
                '': None,
                ' ': None,
                None: None,
                'Ecommerce': '33515',
                'Local': '33516',
                'Mayorista': '33517',
                'B2B': '33518',
                'Showroom Malab': '39036'
                },
            2: {
                '': None,
                ' ': None,
                None: None
                }
            }

services = {
            "login": {
                      "provision": "Usuario",
                      "operacion": "iniciar_sesion"
                    },
            "list_companies": {
                              "provision": "Empresa",
                              "operacion": "listar_empresa"
                              },
            "list_ccost": {
                            "provision": "Empresa",
                            "operacion": "listar_ccostos"
                            },
            "list_diary": {
                           "provision": "Contabilidad",
                           "operacion": "listar_movimientosdiario"
                           },
            "list_invoices": {
                            "provision": "FacturaVenta",
                            "operacion": "listar_facturasventa"
                              },
            "list_inventory": {
                            "provision": "Inventario",
                            "operacion": "listar_itemsinventario"
                            },
            "list_deposits_for_item": {
                            "provision": "Inventario",
                            "operacion": "listar_dispDeposito"
                            },
            }

payload_templates = {
                    "login": {
                        "auth": credentials["dev_user"],
                        "service": services["login"],
                        "parameters": credentials["user"]
                        },
                    "list_companies": {
                                    "auth": credentials["dev_user"],
                                    "service": services["list_companies"],
                                    "parameters": {
                                        "usuario": None,
                                        "password": None,
                                        "sesion": "Dict missing",
                                        "idEmpresa": None,
                                        "idFactura": None,
                                        "fechaDesde": None,
                                        "fechaHasta": None,
                                        "start": 0,
                                        "limit": 10
                                        },
                                    "filter": [{
                                        "field": "IdEmpresa",
                                        "op": "<>",
                                        "value": "1"
                                        }],
                                    "order": {
                                        "field": ["IdEmpresa"],
                                        "order": "asc"
                                        }
                                    },
                    "list_ccost": {
                        "auth": credentials["dev_user"],
                        "service": services["list_ccost"],
                        "parameters": {
                            "sesion": "Dict missing",
                            "idEmpresa": "Company ID str missing",
                            "ccosto": "ccost int missing - 1 or 2"
                        },
                    },
                    "list_diary": {
                            "auth": credentials["dev_user"],
                            "service": services["list_diary"],
                            "parameters": {
                                "sesion": "Dict missing",
                                "idEmpresa": "Company ID str missing",
                                "fromDate": "YYYY-MM-DD str missing",
                                "toDate": "YYYY-MM-DD str missing",
                                "start": 0,
                                "limit": 10000
                                }
                                },
                    "list_invoices": {
                            "auth": credentials["dev_user"],
                            "service": services["list_invoices"],
                            "parameters": {
                                "sesion": "Dict missing",
                                "idEmpresa": "Company ID str missing",
                                "start": 0,
                                "limit": 10000,
                                "filter": [
                                    # TEST FILTER SPECIALLY ON LIMITS
                                    {
                                     "field": "fechaFactura",
                                     "op": ">=",
                                     "value": "start YYYY-MM-DD str missing"
                                    },
                                    {
                                     "field": "fechaFactura",
                                     "op": "<=",
                                     "value": "end YYYY-MM-DD str missing"
                                    },
                                    ],
                                "order": {
                                    "field": [
                                        "idTipoComprobante",
                                        "idFactura"
                                        ],
                                    "order": "asc"
                                        }
                                }
                                      },
                    "list_inventory": {
                            "auth": credentials["dev_user"],
                            "service": services["list_inventory"],
                            "parameters": {
                                "sesion": "Dict missing",
                                "idEmpresa": "Company ID str missing",
                                "start": 0,
                                "limit": 10000,
                                "filter": [],
                                "order": {
                                    "field": "descripcion",
                                    "dir": "ASC"
                                    }
                                }
                            },
                    "list_deposits_for_item": {
                            "auth": credentials["dev_user"],
                            "service": services["list_deposits_for_item"],
                            "parameters": {
                                "idEmpresa": "Company ID str missing",
                                "idItem": "Item ID str missing",
                                "sesion": "Dict missing"
                                }
                            }
                    }

colppy_defaults = {
                  "payload_temps": payload_templates,
                  "ccosts": ccosts,
                  "company_id": company_id
                }
