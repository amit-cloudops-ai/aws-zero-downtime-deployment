import json


def lambda_handler(event, context):
    """
    Blue Lambda - Production Version v1.0.0
    Represents the current stable production environment.
    Part of Blue-Green deployment strategy.
    """
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': 'Hello from Blue environment!',
            'version': 'v1.0.0',
            'environment': 'blue'
        })
    }
