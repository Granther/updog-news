import os
from collections import defaultdict

from app import db
from models import Comment

def get_reply_tree(comment_uuid: str):
    story_id = Comment.query.filter_by(uuid=comment_uuid).first().story_id
    start_comment = Comment.query.filter_by(uuid=comment_uuid).first()
    comments = Comment.query.filter_by(story_id=story_id).order_by(Comment.created).all()

    def build_comment_tree(comments):
        comment_dict = defaultdict(list)
        top_level_comments = []

        for comment in comments:
            if comment.parent_id:
                comment_dict[comment.parent_id].append(comment)
            else:
                top_level_comments.append(comment)

        return top_level_comments, comment_dict
    
    top_level_comments, comment_tree = build_comment_tree(comments)

def get_comment_tree(root_comment_id):
    # Define the base CTE for the root comment
    comment_alias = db.aliased(Comment)
    cte = db.session.query(
        Comment.id,
        Comment.content,
        Comment.parent_id
    ).filter(Comment.id == root_comment_id).cte(name='comment_tree', recursive=True)

    # Define the recursive part of the CTE to get all descendants
    recursive_part = db.session.query(
        comment_alias.id,
        comment_alias.content,
        comment_alias.parent_id
    ).filter(comment_alias.parent_id == cte.c.id)

    # Combine base and recursive parts
    cte = cte.union_all(recursive_part)

    # Query the CTE to get the entire comment tree
    result = db.session.query(cte).all()

    return result