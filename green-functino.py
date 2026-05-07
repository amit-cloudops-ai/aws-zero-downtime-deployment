import json


def lambda_handler(event, context):
    """
    Green Lambda - New Version v2.0.0
    Represents the new version being tested via canary deployment.
    Part of Blue-Green deployment strategy.
    """
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': 'Hello from Green environment!',
            'version': 'v2.0.0',
            'environment': 'green',
            'new_feature': 'Enhanced response format'
        })
    }
