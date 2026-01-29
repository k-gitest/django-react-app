import strawberry
from apps.graphql_api.queries.todo import TodoQuery
from apps.graphql_api.mutations.todo import TodoMutation


@strawberry.type
class Query(TodoQuery):
    """
    GraphQLのルートQuery
    各アプリのQueryを統合
    """
    pass


@strawberry.type
class Mutation(TodoMutation):
    """
    GraphQLのルートMutation
    各アプリのMutationを統合
    """
    pass


schema = strawberry.Schema(query=Query, mutation=Mutation)