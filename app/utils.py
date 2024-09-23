import os
import inspect
from collections import defaultdict

from app import db
from app.models import Comment

def get_reply_tree(comment_uuid: str):
    target_comment = Comment.query.filter_by(uuid=comment_uuid).first()
    story_id = Comment.query.filter_by(uuid=comment_uuid).first().story_id
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
    parents = []

    def get_parent(comment):
        # Use name 
        parents.append({"content": comment.content, "username": comment.user.username})
        for key, value in comment_tree.items():
            for item in value:
                if item.id == comment.parent_id:
                    get_parent(item)

        for com in top_level_comments:
            if com.id == comment.parent_id:
                parents.append(com.content)

        return
    
    get_parent(target_comment)

    return parents

def whoami():
    return inspect.stack()[1][3]

def account_type_owns(comment: Comment) -> str:
    if comment.user:
        return "user"
    elif comment.reporter:
        return "reporter"
    else:
        return None
