



const alignmentStyles = ['left', 'right', 'center'];


class TextAlignment extends window.React.Component {
    render() {
        const createButton = (alignmentText, alignment) => {
            let button = window.React.createElement(window.Draftail.ToolbarButton, {
                name: 'text-align',
                title: alignmentText,
                icon: window.React.createElement('svg', { width: 24, height: 24, viewBox: '0 0 24 24', className: `icon icon-text-${alignment}`},
                    window.React.createElement('use', { href: `#icon-text-${alignment}` })
                ),
                description: alignmentText,
                onClick: () => this.applyAlignment(alignment),
            });
            return button;
        };
        return React.createElement('div', {
                className: 'Draftail-ToolbarGroup',
            },
            createButton(
                this.props.alignmentTextLeft,
                'left'
            ),
            createButton(
                this.props.alignmentTextCenter,
                'center'
            ),
            createButton(
                this.props.alignmentTextRight,
                'right'
            )
        );
    }

    applyAlignment(alignment) {
        const { editorState } = this.props;
        const content = editorState.getCurrentContent();
        const selection = editorState.getSelection();
        
        let styleForRemove = alignmentStyles.filter(style => style !== alignment);
        let focusBlock = content.getBlockForKey(selection.getFocusKey());
        let anchorBlock = content.getBlockForKey(selection.getAnchorKey());
        let isBackward = selection.getIsBackward();
        
        let selectionMerge = {
          anchorOffset: 0,
          focusOffset: focusBlock.getLength(),
        };
        
        if (isBackward) {
          selectionMerge.anchorOffset = anchorBlock.getLength();
        }
        let finalSelection = selection.merge(selectionMerge);
        let finalContent = styleForRemove.reduce((content, style) => 
            window.DraftJS.Modifier.removeInlineStyle(content, finalSelection, style), content);
        
        // Iterate over all blocks in the selection to set alignment data
        let blockKey = finalSelection.getStartKey();
        const endKey = finalSelection.getEndKey();
        do {
          // Add or update block data for alignment
          const blockFromKey = finalContent.getBlockForKey(blockKey);
          const blockData = blockFromKey.getData().merge({ alignment: alignment });
          finalContent = window.DraftJS.Modifier.setBlockData(finalContent, window.DraftJS.SelectionState.createEmpty(blockKey).merge({
            focusKey: blockKey,
            anchorKey: blockKey,
            focusOffset: blockFromKey.getLength(),
            anchorOffset: 0
          }), blockData);
        
          if (blockKey === endKey) {
            break;
          }
        
          blockKey = finalContent.getKeyAfter(blockKey);
        } while (blockKey && finalContent.getBlockForKey(blockKey));
        
        // Apply any inline style changes if necessary
        let modifiedContent = window.DraftJS.Modifier.applyInlineStyle(finalContent, finalSelection, alignment);
        const nextEditorState = window.DraftJS.EditorState.push(editorState, modifiedContent, 'change-inline-style');
        
        this.props.onComplete(nextEditorState);
    }
}


function TextAlignControl({ getEditorState, onChange }) {
    // For script definition see
    // wagtail_hooks/rt_extensions.py
    const translationData = document.getElementById('wagtail-text-alignment-i18n')
    let alignments_i18n;
    if (translationData) {
        alignments_i18n = JSON.parse(
            translationData.textContent,
        );
    } else {
        alignments_i18n = {
            left: "Left",
            center: "Center",
            right: "Right",
        }
    }
    const editorState = getEditorState();

    return React.createElement(TextAlignment, {
        editorState: editorState,
        onComplete: onChange,
        alignmentTextLeft: alignments_i18n['left'],
        alignmentTextCenter: alignments_i18n['center'],
        alignmentTextRight: alignments_i18n['right'],
    });
}


// text-left, text-center, text-right (controls)
window.draftail.registerPlugin({
    type: 'text-alignment',
    inline: TextAlignControl,
}, 'controls');


const blockStyleFn = (block) => {
    let alignment = 'left';

    let data = block.getData();
    if (data.get('alignment')) {
        alignment = data.get('alignment');
    }

    block.findStyleRanges((e) => {
        if (e.hasStyle('center')) {
            alignment = 'center';
        }
        if (e.hasStyle('right')) {
            alignment = 'right';
        }
    });


    return `editor-alignment-${alignment}`;
};


const initEditorProxyTextAlign = new Proxy(window.draftail.initEditor, {
    apply: (target, thisArg, argumentsList) => {
        // Get the target editor in the same way initEditor does and
        // create a partially-applied AIControl component with the
        // element passed as the `field` prop so we can access
        // it later.

        if (!argumentsList[1].plugins) {
            argumentsList[1].plugins = [];
        }

        argumentsList[1].plugins.push({
            type: 'text-align',
            blockStyleFn: blockStyleFn,
        });
      return Reflect.apply(target, thisArg, argumentsList);
    },
});
window.draftail.initEditor = initEditorProxyTextAlign;
