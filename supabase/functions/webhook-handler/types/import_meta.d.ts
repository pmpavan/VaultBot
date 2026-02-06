declare global {
    interface ImportMeta {
        /**
         * A flag indicating if the current module is the main module.
         */
        main: boolean;
        /**
         * The URL of the current module.
         */
        url: string;
    }
}

export { };
