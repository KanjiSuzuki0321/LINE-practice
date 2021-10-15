import os, sys
from linebot import (LineBotApi, WebhookHandler)
from linebot.models import (MessageEvent, TextMessage, TextSendMessage,)
from linebot.exceptions import (LineBotApiError, InvalidSignatureError)
import logging

#-- new line--
import boto3
#-- new line--

logger = logging.getLogger()
logger.setLevel(logging.ERROR)

channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# how does the event look like?
def lambda_handler(event, context):
    signature = event["headers"]["x-line-signature"]
    body = event["body"]

    ok_json = os.environ["ok_json"] # error message as "event" 
    error_json = os.environ["error_json"]

    @handler.add(MessageEvent) 
    # set function which is run when handler gets specific event "MessageEvent"
    def message(line_event):
        # call back
        text = line_event.message.text
        # get the user id who send this message
        user_id = line_event.source.user_id
        
        # access to dynamoDB
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('kanji-practice')
        if(text == "好きです！"):
            try:
                # get record if exit
                record = table.get_item(
                    Key={
                        'id': user_id
                    }
                )
                
                count = int(record['Item']['count'])
                count += 1
                
                table.delete_item(
                    Key={
                        'id': user_id
                    }
                )
                table.put_item(
                       Item={
                            'id': user_id,
                            'count': count,
                        }
                    )
                
                if count == 2:
                    line_bot_api.reply_message(line_event.reply_token, TextSendMessage(text='Umm, No!')) 
                elif count == 3: # say yes if count == 3
                    line_bot_api.reply_message(line_event.reply_token, TextSendMessage(text='Yes!')) 
                else:
                    line_bot_api.reply_message(line_event.reply_token, TextSendMessage(text="Let's break up.")) 
        
            # if not exist, reate new record
            except:
                count = 1
                table.put_item(
                       Item={
                            'id': user_id,
                            'count': count,
                        }
                    )
                line_bot_api.reply_message(line_event.reply_token, TextSendMessage(text='No!')) 
                
        else:
            line_bot_api.reply_message(line_event.reply_token, TextSendMessage(text=text)) 
            
        

    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        logger.error("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            logger.error("  %s: %s" % (m.property, m.message))
        return error_json
    except InvalidSignatureError:
        return error_json
    return ok_json 