import React, { FunctionComponent } from 'react';
import Tooltip from '@mui/material/Tooltip/Tooltip';
import Typography from '@mui/material/Typography/Typography';

type Props = {
    text: string;
};
export const TableText: FunctionComponent<Props> = ({ text }) => {
    return (
        <Tooltip placement="bottom" title={text ?? 'no text'}>
            <Typography
                variant="overline"
                style={{
                    maxWidth: '100px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                }}
            >
                {text}
            </Typography>
        </Tooltip>
    );
};
