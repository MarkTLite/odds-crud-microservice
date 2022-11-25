from concurrent import futures
import odds_crud_pb2_grpc, odds_crud_pb2
import grpc, logging,os

from providers.postgre_provider import PostgresDBProvider

def parse_create_request(request):
    return {'data': (request.league, request.home_team, request.away_team, request.home_team_win_odds, 
            request.away_team_win_odds,request.draw_odds,request.game_date,request.user_id,)}

def parse_update_request(request):
    return {'data': (request.league, request.home_team, request.away_team, request.home_team_win_odds, 
            request.away_team_win_odds,request.draw_odds,request.game_date,request.odds_id,)}

def parse_delete_request(request):
    return {'data': (request.league, request.home_team, request.away_team,request.game_date,)}

def get_range(date_range: 'str'):
    range = date_range.split(' - ')
    return (range[0],range[1],) 

def parse_read_req(req):
    start, stop = get_range(req.date_range) 
    return {'ids': (req.league, start, stop,)}  

def toDataDict(data: 'dict'):
    new_data = []
    for row in data['list']:
        new_data.append(odds_to_datadict(row))
    return new_data

def odds_to_datadict(data_row):
    print(data_row)
    return odds_crud_pb2.DataDict(
        odds_id= str(data_row[0]),
        league = data_row[1],
        home_team = data_row[2],
        away_team = data_row[3],
        home_team_win_odds = float(data_row[4]),
        away_team_win_odds = float(data_row[5]),
        draw_odds = float(data_row[6]),
        game_date = data_row[7]
    )

class OddsCrudServicer(odds_crud_pb2_grpc.OddsCrudServicer):
    """Implements the Crud Logic"""
    def __init__(self) -> None:
        self.provider = PostgresDBProvider()
        self.provider.read_db_config(filename='dbconfig.ini',section='postgresql')
        self.provider.connect()

    def CreateOdds(self, request, context):
        data = parse_create_request(request)  
        response = self.provider.create(location='',data=data)
        return odds_crud_pb2.DBResponse(status=response[0],
                                        message=response[1])
                                        
    def ReadOdds(self, request, context):
        data = parse_read_req(request)  
        response = self.provider.read(location='',data=data)
        for new_data in toDataDict(response[2]):
            yield odds_crud_pb2.DBResponse(status=response[0],
                                            message=response[1],
                                            data=new_data)

    def UpdateOdds(self, request, context):
        data = parse_update_request(request)  
        response = self.provider.update(location='',data=data)
        return odds_crud_pb2.DBResponse(status=response[0],
                                        message=response[1])

    def DeleteOdds(self, request, context):
        data = parse_delete_request(request)  
        response = self.provider.delete(location='',data=data)
        return odds_crud_pb2.DBResponse(status=response[0],
                                        message=response[1])

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    odds_crud_pb2_grpc.add_OddsCrudServicer_to_server(OddsCrudServicer(), server)
    server.add_insecure_port(f'[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    logging.basicConfig()
    serve()