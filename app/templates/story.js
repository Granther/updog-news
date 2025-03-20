console.log("here");

var comment_section = document.getElementById('comment-section');

fetch(`{{url_for('main.comments', uuid=uuid)}}`)
.then(response => response.json())
.then(data => {
    const top_level_comments = data.top_level_comments;
    const comment_tree = data.comment_tree;

    top_level_comments.forEach(comment => {
        render_comment(comment, comment_tree);
    });
})
.catch((error) => {
    console.log(error);
});

function render_comment(comment, comment_tree, parent = null) {
    const commentElement = document.createElement('div');
    commentElement.classList = "flex flex-col justify-left text-black w-full"
    commentElement.classList.add('comment', 'p-6', 'mb-4');
    // commentElement.innerHTML = `
    //     <div class="flex flex-col">
    //         <p class="text-gray-900 dark:text-white">${comment.content}</p>
    //         <button class="reply-btn bg-sky-500 hover:bg-sky-700 text-white rounded-full text-sm right-0 ml-auto">Reply</button>
    //     </div>
    //     <form class="reply-form hidden" data-parent-id="${comment.id}" data-story-id="{{ uuid }}">
    //         <textarea class="reply-input mt-2 w-full p-2 rounded border"></textarea>
    //         <button type="submit" class="submit-reply bg-sky-500 hover:bg-sky-700 text-white py-1 px-3 rounded-full text-sm mt-2">Submit Reply</button>
    //     </form>
    // `;

    commentElement.innerHTML = `    
    <article class="p-6 mb-6 ml-6 lg:ml-12 text-base bg-white rounded-lg dark:bg-gray-800 shadow-md">
        <footer class="flex justify-between items-center mb-4">
            <div class="flex items-center">
                <p class="inline-flex items-center mr-4 text-sm font-semibold text-gray-900 dark:text-white">
                    <img class="mr-2 w-8 h-8 rounded-full" src="https://flowbite.com/docs/images/people/profile-picture-5.jpg" alt="User avatar">${comment.username}
                </p>
            </div>
        </footer>
        <p class="text-gray-700 dark:text-gray-300 leading-relaxed">${comment.content}</p>
        <div class="flex items-center mt-4 space-x-4">
            <button type="button"
                class="reply-btn flex items-center text-sm font-medium text-sky-600 hover:text-sky-800 dark:text-sky-400 dark:hover:text-sky-600 transition-colors duration-200">
                <svg class="mr-2 w-4 h-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 18" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 5h5M5 8h2m6-3h2m-5 3h6m2-7H2a1 1 0 0 0-1 1v9a1 1 0 0 0 1 1h3v5l5-5h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1Z"/>
                </svg>                
                Reply
            </button>
        </div>
        <form class="reply-form hidden mt-4" data-parent-id="${comment.id}" data-story-id="{{ uuid }}">
            <textarea class="reply-input w-full p-3 text-gray-800 dark:text-gray-300 dark:bg-gray-700 border rounded-md focus:ring-sky-500 focus:border-sky-500" placeholder="Write your reply..."></textarea>
            <button type="submit" class="submit-reply mt-3 bg-sky-500 hover:bg-sky-600 text-white py-2 px-4 rounded-full text-sm transition-colors duration-200">
                Submit Reply
            </button>
        </form>
    </article>
    `;

    // If there is a parent, append it to the parent's comment
    if (parent) {
        parent.appendChild(commentElement);
    } else {
        comment_section.appendChild(commentElement);
    }

    // Event listener for "Reply" button
    const replyBtn = commentElement.querySelector('.reply-btn');
    replyBtn.addEventListener('click', function(event) {
        event.preventDefault()
        const replyForm = commentElement.querySelector('.reply-form');
        replyForm.classList.toggle('hidden'); // Show or hide reply form
    });

    const likeBtn = document.getElementById('like-btn')
    console.log(likeBtn)
    likeBtn.addEventListener('click', function(event) {
        // event.preventDefault()
        console.log("clicked")
    });

    // Event listener for submitting reply
    const replyForm = commentElement.querySelector('.reply-form');
    replyForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const replyContent = replyForm.querySelector('.reply-input').value;
        const parentId = replyForm.dataset.parentId;
        const storyId = replyForm.dataset.storyId;
        reply({parent_id: parentId, reply: replyContent, story_id: storyId});
    });

    // Render child comments (replies)
    const children = comment_tree[comment.id];
    if (children && children.length > 0) {
        children.forEach(childComment => {
            render_comment(childComment, comment_tree, commentElement);
        });
    }
}

// Function to handle the reply form submission
function reply(json) {
    fetch(`{{url_for('main.reply')}}`, {
            method: 'POST',
            body: JSON.stringify(json),
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            // Refresh the comment section after reply is submitted
            // location.reload();
        })
        .catch(error => {
            console.log('Error occurred while submitting reply:', error);
        });
}

document.getElementById('comment-box').addEventListener("submit", function(event) {
    event.preventDefault();
    // var formData = new FormData(this);
    // console.log(formData)

    var data = {comment: this.comment.value}
    console.log(data.comment)

    fetch(`{{url_for('main.comment', uuid=uuid)}}`, {
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
    }).then(response => response.json())
    .then(data => {
        location.reload();
    }).catch(error => {
        console.log("Error occurred while submitting comment:", error);
    });
});
